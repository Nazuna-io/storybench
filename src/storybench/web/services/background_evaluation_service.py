"""
Background evaluation service that processes evaluations from the web UI.
Monitors database for new evaluations and processes them using the same core logic as CLI.
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

logger = logging.getLogger(__name__)

class BackgroundEvaluationService:
    """Background service that processes evaluations created by the web UI."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.runner = DatabaseEvaluationRunner(database)
        
        # Get OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for evaluation processing")
            
        self.sequence_service = SequenceEvaluationService(database, openai_api_key)
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
                # Check if this evaluation has any responses (indicating processing started)
                existing_responses = await self.database.responses.count_documents({
                    "evaluation_id": str(evaluation.id)
                })
                
                if existing_responses == 0:
                    # This is a fresh evaluation, start processing it
                    logger.info(f"Starting processing for evaluation {evaluation.id}")
                    await self._process_evaluation(evaluation)
                    
        except Exception as e:
            logger.error(f"Error processing pending evaluations: {e}")
            
    async def _process_evaluation(self, evaluation):
        """Process a single evaluation using the same logic as CLI."""
        try:
            evaluation_id = str(evaluation.id)
            
            # Get configuration from the evaluation
            models = evaluation.models
            global_settings = evaluation.global_settings.model_dump()
            
            # Get sequences and criteria from config service
            config_service = self.runner.config_service
            prompts_config = await config_service.get_active_prompts()
            criteria_config = await config_service.get_active_criteria()
            
            if not prompts_config or not criteria_config:
                logger.error(f"Missing configuration for evaluation {evaluation_id}")
                await self.runner.mark_evaluation_failed(evaluation.id, "Missing prompts or criteria configuration")
                return
                
            sequences = {name: [prompt.model_dump() for prompt in prompt_list] 
                        for name, prompt_list in prompts_config.sequences.items()}
            criteria = {name: criterion.model_dump() for name, criterion in criteria_config.criteria.items()}
            
            # Update evaluation status to show processing started
            await self.runner.evaluation_repo.update_by_id(
                evaluation.id, 
                {"current_model": models[0] if models else "Unknown"}
            )
            
            # Process each model
            for model_name in models:
                logger.info(f"Processing model {model_name} for evaluation {evaluation_id}")
                
                # Update current model in database
                await self.runner.evaluation_repo.update_by_id(
                    evaluation.id,
                    {"current_model": model_name}
                )
                
                # Process sequences for this model using existing service
                await self.sequence_service.process_model_sequences(
                    evaluation_id=evaluation_id,
                    model_name=model_name,
                    sequences=sequences,
                    criteria=criteria,
                    global_settings=global_settings
                )
                
            # Mark evaluation as completed
            await self.runner.mark_evaluation_completed(evaluation.id)
            logger.info(f"Completed evaluation {evaluation_id}")
            
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
