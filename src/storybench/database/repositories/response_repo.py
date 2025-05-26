"""Response repository for managing model response documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models import Response, ResponseStatus
from .base import BaseRepository

class ResponseRepository(BaseRepository[Response]):
    """Repository for model response documents."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, Response)
        
    def _get_collection_name(self) -> str:
        return "responses"
        
    async def find_by_evaluation_id(self, evaluation_id: ObjectId) -> List[Response]:
        """Find all responses for an evaluation."""
        return await self.find_many({"evaluation_id": evaluation_id})
        
    async def find_incomplete_for_evaluation(self, evaluation_id: ObjectId) -> List[dict]:
        """Find incomplete tasks for resuming evaluation."""
        # This would return missing combinations of (model, sequence, run, prompt_index)
        pipeline = [
            {"$match": {"evaluation_id": evaluation_id}},
            {"$group": {
                "_id": {
                    "model_name": "$model_name",
                    "sequence": "$sequence", 
                    "run": "$run",
                    "prompt_index": "$prompt_index"
                }
            }}
        ]
        
        completed_tasks = []
        async for doc in self.collection.aggregate(pipeline):
            completed_tasks.append(doc["_id"])
            
        return completed_tasks
        
    async def count_by_evaluation_id(self, evaluation_id: ObjectId) -> int:
        """Count responses for an evaluation."""
        # Handle both ObjectId and string format
        evaluation_id_str = str(evaluation_id)
        return await self.collection.count_documents({"evaluation_id": evaluation_id_str})
