"""Evaluation repository for managing evaluation documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models import Evaluation, EvaluationStatus
from .base import BaseRepository

class EvaluationRepository(BaseRepository[Evaluation]):
    """Repository for evaluation documents."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, Evaluation)
        
    def _get_collection_name(self) -> str:
        return "evaluations"
        
    async def find_by_config_hash(self, config_hash: str) -> List[Evaluation]:
        """Find evaluations by configuration hash."""
        return await self.find_many({"config_hash": config_hash})
        
    async def find_by_status(self, status: EvaluationStatus) -> List[Evaluation]:
        """Find evaluations by status."""
        return await self.find_many({"status": status.value})
        
    async def find_incomplete(self) -> List[Evaluation]:
        """Find all incomplete evaluations."""
        return await self.find_many({
            "status": {"$in": [EvaluationStatus.IN_PROGRESS.value, EvaluationStatus.PAUSED.value]}
        })
        
    async def update_progress(self, evaluation_id: ObjectId, 
                            completed_tasks: int,
                            current_model: str = None,
                            current_sequence: str = None,
                            current_run: int = None) -> bool:
        """Update evaluation progress."""
        update_data = {"completed_tasks": completed_tasks}
        
        if current_model is not None:
            update_data["current_model"] = current_model
        if current_sequence is not None:
            update_data["current_sequence"] = current_sequence
        if current_run is not None:
            update_data["current_run"] = current_run
            
        return await self.update_by_id(evaluation_id, update_data)
        
    async def mark_completed(self, evaluation_id: ObjectId) -> bool:
        """Mark evaluation as completed."""
        from datetime import datetime
        return await self.update_by_id(evaluation_id, {
            "status": EvaluationStatus.COMPLETED.value,
            "completed_at": datetime.utcnow()
        })
        
    async def mark_failed(self, evaluation_id: ObjectId, error_message: str) -> bool:
        """Mark evaluation as failed with error message."""
        return await self.update_by_id(evaluation_id, {
            "status": EvaluationStatus.FAILED.value,
            "error_message": error_message
        })
