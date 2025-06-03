"""Evaluation service for managing evaluation lifecycle."""

from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from ..models import Evaluation, EvaluationStatus, Response, GlobalSettings
from ..repositories import EvaluationRepository, ResponseRepository

class EvaluationService:
    """Service for managing evaluation lifecycle and progress."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.evaluation_repo = EvaluationRepository(database)
        self.response_repo = ResponseRepository(database)
        
    async def create_evaluation(self, 
                               config_hash: str,
                               models: List[str],
                               global_settings: GlobalSettings,
                               total_tasks: int) -> Evaluation:
        """Create a new evaluation."""
        evaluation = Evaluation(
            config_hash=config_hash,
            models=models,
            global_settings=global_settings,
            total_tasks=total_tasks,
            status=EvaluationStatus.IN_PROGRESS
        )
        
        return await self.evaluation_repo.create(evaluation)
        
    async def find_incomplete_evaluations(self) -> List[Evaluation]:
        """Find all incomplete evaluations for resume functionality."""
        return await self.evaluation_repo.find_incomplete()
        
    async def get_evaluation_progress(self, evaluation_id: ObjectId) -> Dict[str, Any]:
        """Get detailed progress information for an evaluation with enhanced statistics."""
        evaluation = await self.evaluation_repo.find_by_id(evaluation_id)
        if not evaluation:
            return None
            
        # Use optimized statistics query for comprehensive information
        stats = await self.response_repo.get_evaluation_statistics(evaluation_id)
        completed_count = stats["total_count"]
        
        return {
            "evaluation_id": str(evaluation_id),
            "status": evaluation.status,
            "total_tasks": evaluation.total_tasks,
            "completed_tasks": completed_count,
            "progress_percent": (completed_count / evaluation.total_tasks * 100) if evaluation.total_tasks > 0 else 0,
            "current_model": evaluation.current_model,
            "current_sequence": evaluation.current_sequence,
            "current_run": evaluation.current_run,
            "started_at": evaluation.started_at,
            "completed_at": evaluation.completed_at,
            # Enhanced statistics from optimized query
            "model_count": stats["model_count"],
            "sequence_count": stats["sequence_count"],
            "avg_generation_time": stats["avg_generation_time"],
            "total_generation_time": stats["total_generation_time"],
            "by_model_count": stats["by_model_count"]
        }
        
    async def save_response(self, evaluation_id: ObjectId, 
                           model_name: str,
                           sequence: str,
                           run: int,
                           prompt_index: int,
                           prompt_name: str,
                           prompt_text: str,
                           response_text: str,
                           generation_time: float) -> Response:
        """Save a model response."""
        response = Response(
            evaluation_id=evaluation_id,
            model_name=model_name,
            sequence=sequence,
            run=run,
            prompt_index=prompt_index,
            prompt_name=prompt_name,
            prompt_text=prompt_text,
            response=response_text,
            generation_time=generation_time
        )
        
        return await self.response_repo.create(response)
        
    async def update_evaluation_progress(self, evaluation_id: ObjectId,
                                       current_model: str = None,
                                       current_sequence: str = None,
                                       current_run: int = None) -> bool:
        """Update evaluation progress indicators with optimized query."""
        # Use optimized statistics query instead of simple count
        stats = await self.response_repo.get_evaluation_statistics(evaluation_id)
        completed_count = stats["total_count"]
        
        return await self.evaluation_repo.update_progress(
            evaluation_id, 
            completed_count,
            current_model,
            current_sequence,
            current_run
        )
