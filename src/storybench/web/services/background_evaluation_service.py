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
                # Check if this evaluation has any progress yet
                progress = await self.runner.get_evaluation_progress(evaluation.id)
                
                if progress and progress.get("completed_tasks", 0) == 0:
                    # This is a fresh evaluation, start processing it
                    logger.info(f"Starting processing for evaluation {evaluation.id}")
                    # Start processing in background task so we don't block polling
                    asyncio.create_task(self._process_evaluation(evaluation))
                    
        except Exception as e:
            logger.error(f"Error processing pending evaluations: {e}")
    
    async def _process_evaluation(self, evaluation):
        """Process a single evaluation - simplified simulation for testing."""
        try:
            evaluation_id = str(evaluation.id)
            models = evaluation.models
            total_tasks = evaluation.total_tasks
            
            logger.info(f"Starting processing for evaluation {evaluation_id}")
            
            # Simulate processing each model with progress updates
            completed_tasks = 0
            
            for i, model_name in enumerate(models):
                logger.info(f"Processing model {model_name} for evaluation {evaluation_id}")
                
                # Update current model in database
                await self.runner.evaluation_repo.update_by_id(
                    evaluation.id,
                    {
                        "current_model": model_name,
                        "current_sequence": "FilmNarrative",
                        "current_run": 1,
                        "completed_tasks": completed_tasks
                    }
                )
                
                # Simulate processing time with progress updates
                tasks_per_model = max(1, total_tasks // len(models)) if models else 1
                for j in range(tasks_per_model):
                    completed_tasks += 1
                    
                    # Update progress
                    await self.runner.evaluation_repo.update_by_id(
                        evaluation.id,
                        {"completed_tasks": completed_tasks}
                    )
                    
                    # Wait a bit to simulate work
                    await asyncio.sleep(3)
                    
                    logger.info(f"Progress: {completed_tasks}/{total_tasks} tasks completed")
            
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
