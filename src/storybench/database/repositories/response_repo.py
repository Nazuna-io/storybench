"""Response repository for managing model response documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models import Response, ResponseStatus
from .base import BaseRepository
from ...utils.performance import monitor_query_performance

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
        
    @monitor_query_performance("response_count_by_evaluation")
    async def count_by_evaluation_id(self, evaluation_id: ObjectId) -> int:
        """Count responses for an evaluation with optimized query."""
        # Handle both ObjectId and string format
        evaluation_id_str = str(evaluation_id)
        return await self.collection.count_documents({"evaluation_id": evaluation_id_str})
        
    @monitor_query_performance("response_evaluation_statistics") 
    async def get_evaluation_statistics(self, evaluation_id: ObjectId) -> dict:
        """Get comprehensive evaluation statistics in a single query.
        
        Returns statistics including total count, counts by model, sequence, etc.
        This replaces multiple separate count queries with one aggregation.
        """
        evaluation_id_str = str(evaluation_id)
        
        pipeline = [
            {"$match": {"evaluation_id": evaluation_id_str}},
            {
                "$group": {
                    "_id": None,
                    "total_count": {"$sum": 1},
                    "by_model": {
                        "$push": {
                            "model": "$model_name",
                            "sequence": "$sequence", 
                            "run": "$run"
                        }
                    },
                    "unique_models": {"$addToSet": "$model_name"},
                    "unique_sequences": {"$addToSet": "$sequence"},
                    "avg_generation_time": {"$avg": "$generation_time"},
                    "total_generation_time": {"$sum": "$generation_time"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_count": 1,
                    "model_count": {"$size": "$unique_models"},
                    "sequence_count": {"$size": "$unique_sequences"},
                    "avg_generation_time": 1,
                    "total_generation_time": 1,
                    "by_model_count": {
                        "$reduce": {
                            "input": "$unique_models",
                            "initialValue": {},
                            "in": {
                                "$mergeObjects": [
                                    "$$value",
                                    {
                                        "$$this": {
                                            "$size": {
                                                "$filter": {
                                                    "input": "$by_model",
                                                    "cond": {"$eq": ["$$item.model", "$$this"]}
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        else:
            return {
                "total_count": 0,
                "model_count": 0,
                "sequence_count": 0,
                "avg_generation_time": 0,
                "total_generation_time": 0,
                "by_model_count": {}
            }
            
    @monitor_query_performance("response_bulk_create")
    async def bulk_create(self, responses: List[Response]) -> List[Response]:
        """Create multiple responses in a single batch operation."""
        if not responses:
            return []
            
        # Convert to documents
        documents = []
        for response in responses:
            doc = response.model_dump()
            documents.append(doc)
        
        # Batch insert
        result = await self.collection.insert_many(documents)
        
        # Update responses with inserted IDs
        for i, response in enumerate(responses):
            response.id = result.inserted_ids[i]
            
        return responses
