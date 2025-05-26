"""
Background evaluation service that processes evaluations from the web UI.
Monitors database for new evaluations and processes them using simplified simulation.
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
        if self.is_running:
            logger.warning("Background evaluation service is already running")
            return
            
        self.is_running = True
        self._stop_event.clear()
        logger.info("Starting background evaluation service...")
        
        # Main service loop
        try:
            while not self._stop_event.is_set():
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
            # Find evaluations that are in_progress but haven't started processing
            pending_evaluations = await self.runner.find_running_evaluations()
            
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
        """Process a single evaluation - creates actual response records."""
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
            
            num_runs = 3  # Default number of runs
            completed_tasks = 0
            
            for model_name in models:
                logger.info(f"Processing model {model_name} for evaluation {evaluation_id}")
                
                for sequence_name, prompts in sequences.items():
                    logger.info(f"Processing sequence {sequence_name} with {len(prompts)} prompts")
                    
                    for run in range(1, num_runs + 1):
                        for prompt_index, prompt in enumerate(prompts):
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
                            
                            # Create simulated response
                            response_text = f"Simulated response from {model_name} for prompt '{prompt['name']}' in sequence '{sequence_name}' (Run {run})"
                            
                            # Save the response to database
                            await self.runner.save_response(
                                evaluation_id=str(evaluation_id),  # Convert ObjectId to string
                                model_name=model_name,
                                sequence=sequence_name,
                                run=run,
                                prompt_index=prompt_index,
                                prompt_name=prompt["name"],
                                prompt_text=prompt["text"],
                                response_text=response_text,
                                generation_time=2.5  # Simulated generation time
                            )
                            
                            completed_tasks += 1
                            
                            # Simulate processing time
                            await asyncio.sleep(2)
                            
                            logger.info(f"Progress: {completed_tasks}/{evaluation.total_tasks} tasks completed")
            
            # Mark evaluation as completed
            await self.runner.mark_evaluation_completed(evaluation_id)
            logger.info(f"Completed evaluation {evaluation_id} with {completed_tasks} responses")
            
        except Exception as e:
            logger.error(f"Error processing evaluation {evaluation.id}: {e}")
            await self.runner.mark_evaluation_failed(evaluation.id, str(e))

# Global service instance
_background_service: Optional[BackgroundEvaluationService] = None

async def get_background_service() -> BackgroundEvaluationService:
    """Get or create the background evaluation service."""
    global _background_service
    if _background_service is None:
        database = await get_database()
        _background_service = BackgroundEvaluationService(database)
    return _background_service

async def start_background_service():
    """Start the background evaluation service."""
    service = await get_background_service()
    if not service.is_running:
        # Start in background task
        asyncio.create_task(service.start())

async def stop_background_service():
    """Stop the background evaluation service."""
    global _background_service
    if _background_service and _background_service.is_running:
        await _background_service.stop()
