"""
Background evaluation service that processes evaluations from the web UI.
Monitors database for new evaluations and processes them using real LLM APIs and evaluations.
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...database.connection import get_database
from ...database.models import EvaluationStatus
from ...database.services.evaluation_runner import DatabaseEvaluationRunner
from ...database.services.sequence_evaluation_service import SequenceEvaluationService
from ...database.repositories.criteria_repo import CriteriaRepository
from ...evaluators.factory import EvaluatorFactory

logger = logging.getLogger(__name__)

class BackgroundEvaluationService:
    """Background service that processes evaluations created by the web UI."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.runner = DatabaseEvaluationRunner(database)
        self.is_running = False
        self._stop_event = asyncio.Event()
        
    async def start(self):
        """Start the background evaluation service."""
        logger.info("[DEBUG] Entered BackgroundEvaluationService.start()")
        if self.is_running:
            logger.warning("Background evaluation service is already running")
            return
            
        self.is_running = True
        self._stop_event.clear()
        logger.info("Starting background evaluation service...")
        
        # Main service loop
        try:
            while not self._stop_event.is_set():
                logger.info("[DEBUG] BackgroundEvaluationService main loop running...")
                await self._process_pending_evaluations()
                # Check every 5 seconds for new evaluations
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=5.0)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    continue  # Timeout, continue polling
                    
        except Exception as e:
            logger.error(f"Background evaluation service error: {e}")
        finally:
            self.is_running = False
            logger.info("Background evaluation service stopped")
            
    async def stop(self):
        """Stop the background evaluation service."""
        logger.info("Stopping background evaluation service...")
        self._stop_event.set()
        
    async def _process_pending_evaluations(self):
        """Check for and process any pending evaluations."""
        try:
            now = datetime.utcnow().isoformat()
            pending_evaluations = await self.runner.find_running_evaluations()
            logger.info(f"[HEARTBEAT] _process_pending_evaluations at {now}: found {len(pending_evaluations)} pending evaluations.")
            
            for evaluation in pending_evaluations:
                # Check if this evaluation has any responses yet
                response_count = await self.database.responses.count_documents({
                    "evaluation_id": str(evaluation.id)
                })
                
                # Only process if:
                # 1. No responses exist yet (fresh evaluation)
                # 2. OR evaluation was interrupted and needs resuming
                if response_count == 0:
                    # This is a fresh evaluation, start processing it
                    logger.info(f"Starting processing for fresh evaluation {evaluation.id}")
                    # Start processing in background task so we don't block polling
                    asyncio.create_task(self._process_evaluation(evaluation))
                elif response_count < evaluation.total_tasks:
                    # This is a partially completed evaluation - could be resumed  
                    logger.info(f"Found partially completed evaluation {evaluation.id} ({response_count}/{evaluation.total_tasks} responses)")
                    # For now, we'll skip automatic resume to avoid conflicts
                    # User should explicitly choose to resume via UI
                else:
                    # This evaluation appears complete but status is still in_progress
                    # Mark it as completed
                    logger.info(f"Marking completed evaluation {evaluation.id} as finished")
                    await self.runner.mark_evaluation_completed(evaluation.id)
                    
        except Exception as e:
            logger.error(f"Error processing pending evaluations: {e}")
    
    async def _process_evaluation(self, evaluation):
        """Process a single evaluation - creates actual response records using real LLM APIs."""
        try:
            evaluation_id = evaluation.id
            models = evaluation.models
            
            logger.info(f"Starting processing for evaluation {evaluation_id}")
            
            # Get the actual sequences from the evaluation's stored configuration
            # We need to reconstruct this from the active configuration
            from ...database.services.config_service import ConfigService
            config_service = ConfigService(self.database)
            
            try:
                # Get the current active prompts configuration
                prompts_config = await config_service.get_active_prompts()
                if prompts_config and hasattr(prompts_config, 'sequences'):
                    sequences = {name: [prompt.model_dump() for prompt in prompt_list] 
                               for name, prompt_list in prompts_config.sequences.items()}
                else:
                    # Fallback to hardcoded sequences if config is missing
                    logger.warning("No prompts config found, using fallback sequences")
                    sequences = {
                        "FilmNarrative": [
                            {"name": "Initial Concept", "text": "Create a feature film concept..."},
                            {"name": "Character Development", "text": "Develop the main characters..."},
                            {"name": "Plot Structure", "text": "Outline the plot structure..."}
                        ]
                    }
            except Exception as config_error:
                logger.error(f"Error loading prompts config: {config_error}")
                # Use minimal fallback
                sequences = {
                    "FilmNarrative": [
                        {"name": "Initial Concept", "text": "Create a feature film concept..."},
                        {"name": "Scene Development", "text": "Develop a pivotal scene..."},
                        {"name": "Visual Realization", "text": "Describe the most striking visual..."}
                    ]
                }
            
            # Get API keys from environment
            api_keys = self._get_api_keys()
            
            num_runs = 3  # Default number of runs
            completed_tasks = 0
            
            # Update evaluation status to response generation phase
            await self.runner.evaluation_repo.update_by_id(
                evaluation_id,
                {"status": EvaluationStatus.GENERATING_RESPONSES}
            )
            
            # Build complete response generation plan - ONE evaluation with ALL responses
            response_plan = []
            for model_name in models:
                for sequence_name, prompts in sequences.items():
                    for run in range(1, num_runs + 1):
                        for prompt_index, prompt in enumerate(prompts):
                            response_plan.append({
                                "model_name": model_name,
                                "sequence_name": sequence_name,
                                "run": run,
                                "prompt_index": prompt_index,
                                "prompt": prompt
                            })
            
            total_responses = len(response_plan)
            logger.info(f"Response generation plan: {total_responses} total responses for evaluation {evaluation_id}")
            logger.info(f"Plan breakdown: {len(models)} models × {len(sequences)} sequences × {num_runs} runs × {len(list(sequences.values())[0]) if sequences else 0} prompts")
            
            any_responses_generated = False
            model_evaluators = {}  # Cache evaluators to avoid recreating them
            
            # Process each response in the unified plan
            for plan_item in response_plan:
                model_name = plan_item["model_name"]
                sequence_name = plan_item["sequence_name"]
                run = plan_item["run"]
                prompt_index = plan_item["prompt_index"]
                prompt = plan_item["prompt"]
                
                # Update current status
                await self.runner.evaluation_repo.update_by_id(
                    evaluation_id,
                    {
                        "current_model": model_name,
                        "current_sequence": sequence_name,
                        "current_run": run,
                        "completed_tasks": completed_tasks
                    }
                )
                
                # Get or create evaluator for this model (cache to avoid repeated setup)
                if model_name not in model_evaluators:
                    logger.info(f"Setting up evaluator for model {model_name}")
                    
                    # Get model configuration from database
                    models_config = await config_service.get_active_models()
                    if not models_config:
                        logger.error(f"No active models configuration found")
                        continue
                    
                    # Find the specific model configuration
                    model_config = None
                    for model in models_config.models:
                        if model.name == model_name:
                            model_config = {
                                "type": model.type,
                                "provider": model.provider,
                                "model_name": model.model_name
                            }
                            break
                    
                    if not model_config:
                        logger.error(f"Model configuration not found for {model_name}")
                        model_evaluators[model_name] = None
                        continue
                    
                    # Create evaluator for this model
                    try:
                        evaluator = EvaluatorFactory.create_evaluator(model_name, model_config, api_keys)
                        setup_success = await evaluator.setup()
                        if not setup_success:
                            logger.error(f"Failed to setup evaluator for {model_name}")
                            model_evaluators[model_name] = None
                            continue
                        model_evaluators[model_name] = evaluator
                    except Exception as e:
                        logger.error(f"Failed to create evaluator for {model_name}: {e}")
                        model_evaluators[model_name] = None
                        continue
                
                evaluator = model_evaluators.get(model_name)
                if not evaluator:
                    logger.warning(f"No evaluator available for {model_name}, skipping response")
                    continue
                
                # Generate real response using LLM API
                try:
                    logger.info(f"Generating response {completed_tasks + 1}/{total_responses}: {model_name}/{sequence_name}/run{run}/{prompt['name']}")
                    start_time = datetime.now()
                    response_result = await evaluator.generate_response(prompt['text'])
                    end_time = datetime.now()
                    generation_time = (end_time - start_time).total_seconds()
                    
                    # Extract response text from the result dict
                    response_text = response_result.get("response", "")
                    
                    # Save the response to database - ALL responses belong to the SAME evaluation
                    await self.runner.save_response(
                        evaluation_id=str(evaluation_id),  # Convert ObjectId to string
                        model_name=model_name,
                        sequence=sequence_name,
                        run=run,
                        prompt_index=prompt_index,
                        prompt_name=prompt["name"],
                        prompt_text=prompt["text"],
                        response_text=response_text,
                        generation_time=generation_time
                    )
                    any_responses_generated = True
                    completed_tasks += 1
                    logger.info(f"Generated response ({generation_time:.1f}s) - Progress: {completed_tasks}/{total_responses}")
                    
                    # Update evaluation progress
                    await self.runner.evaluation_repo.update_by_id(
                        evaluation_id,
                        {"completed_tasks": completed_tasks}
                    )
                    
                    # Add delay to be nice to APIs
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error generating response for {model_name}/{sequence_name}/run{run}/{prompt['name']}: {e}")
                    # Continue with next response even if one fails
                    continue
            
            # Cleanup all evaluators
            for model_name, evaluator in model_evaluators.items():
                if evaluator:
                    try:
                        await evaluator.cleanup()
                    except Exception as e:
                        logger.warning(f"Error cleaning up evaluator for {model_name}: {e}")
            
            # Summary of response generation phase
            logger.info(f"Response generation completed for evaluation {evaluation_id}")
            logger.info(f"✅ Generated {completed_tasks}/{total_responses} responses successfully")
            
            # If no responses were generated, mark evaluation as failed and exit
            if not any_responses_generated:
                logger.error(f"No responses were generated for evaluation {evaluation_id}. Marking as FAILED.")
                await self.runner.mark_evaluation_failed(
                    evaluation_id,
                    "No responses were generated for any model. All models may have failed or been rate-limited."
                )
                return
            
            # If some responses failed, log warning but continue
            if completed_tasks < total_responses:
                failed_count = total_responses - completed_tasks
                logger.warning(f"⚠️  {failed_count} responses failed to generate, but continuing with {completed_tasks} successful responses")

            # Update evaluation status to responses complete
            await self.runner.evaluation_repo.update_by_id(
                evaluation_id,
                {"status": EvaluationStatus.RESPONSES_COMPLETE}
            )
            logger.info(f"Response generation complete for evaluation {evaluation_id}")
            
            # Update evaluation status to LLM evaluation phase
            await self.runner.evaluation_repo.update_by_id(
                evaluation_id,
                {"status": EvaluationStatus.EVALUATING_RESPONSES}
            )
            
            # Step 2: Run LLM evaluation on all generated responses
            logger.info(f"Starting LLM evaluation for evaluation {evaluation_id}")
            
            # Check if we have OpenAI API key for evaluation
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.error("OPENAI_API_KEY not found - cannot run LLM evaluation")
                await self.runner.mark_evaluation_failed(evaluation_id, "OPENAI_API_KEY not found for LLM evaluation")
                return
            
            # Initialize sequence evaluation service
            sequence_eval_service = SequenceEvaluationService(self.database, openai_api_key)
            
            # Check if we have active criteria
            criteria_repo = CriteriaRepository(self.database)
            active_criteria = await criteria_repo.find_active()
            
            if not active_criteria:
                logger.error("No active evaluation criteria found")
                await self.runner.mark_evaluation_failed(evaluation_id, "No active evaluation criteria found")
                return
            
            logger.info(f"Using criteria version {active_criteria.version}")
            
            # Run sequence-aware evaluations
            try:
                eval_results = await sequence_eval_service.evaluate_all_sequences()
                logger.info(f"LLM evaluation complete - Sequences evaluated: {eval_results['sequences_evaluated']}, Total evaluations: {eval_results['total_evaluations_created']}")
                
                if eval_results.get('errors'):
                    logger.warning(f"LLM evaluation had {len(eval_results['errors'])} errors")
                    for error in eval_results['errors'][:3]:  # Log first 3 errors
                        logger.warning(f"Evaluation error: {error}")
                
            except Exception as e:
                logger.error(f"Error during LLM evaluation: {e}")
                await self.runner.mark_evaluation_failed(evaluation_id, f"LLM evaluation failed: {str(e)}")
                return
            
            # Mark evaluation as completed only after both response generation AND evaluation are done
            await self.runner.mark_evaluation_completed(evaluation_id)
            logger.info(f"Completed evaluation {evaluation_id} with {completed_tasks} responses and LLM evaluations")
            
        except Exception as e:
            logger.error(f"Error processing evaluation {evaluation.id}: {e}")
            await self.runner.mark_evaluation_failed(evaluation.id, str(e))
    
    def _get_api_keys(self) -> Dict[str, str]:
        """Get API keys from environment variables."""
        api_keys = {}
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            api_keys["openai"] = os.getenv("OPENAI_API_KEY")
        
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            api_keys["anthropic"] = os.getenv("ANTHROPIC_API_KEY")
        
        # Google Gemini
        if os.getenv("GOOGLE_API_KEY"):
            api_keys["google"] = os.getenv("GOOGLE_API_KEY")
        
        return api_keys

# Global service instance
_background_service: Optional[BackgroundEvaluationService] = None

import logging

async def get_background_service() -> Optional[BackgroundEvaluationService]:
    """Get or create the background evaluation service."""
    global _background_service
    if _background_service is None:
        try:
            database = await get_database()
            logging.info("[DEBUG] Creating new BackgroundEvaluationService instance.")
            _background_service = BackgroundEvaluationService(database)
        except Exception as e:
            logging.error(f"Failed to get database for background service: {e}")
            return None
    return _background_service

async def start_background_service():
    """Start the background evaluation service."""
    service = await get_background_service()
    if service and not service.is_running:
        # Start in background task
        asyncio.create_task(service.start())

async def stop_background_service():
    """Stop the background evaluation service."""
    global _background_service
    if _background_service and _background_service.is_running:
        await _background_service.stop()
