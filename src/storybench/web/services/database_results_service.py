"""Database-based results service for evaluation data."""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..repositories.evaluation_repo import EvaluationRepository
from ..repositories.response_repo import ResponseRepository


class DatabaseResultsService:
    """Service for retrieving evaluation results from database."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.evaluation_repo = EvaluationRepository(database)
        self.response_repo = ResponseRepository(database)
        
    async def get_all_results(self, config_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all evaluation results with optional filtering."""
        try:
            # Get completed evaluations
            filter_criteria = {"status": "completed"}
            if config_version:
                filter_criteria["config_hash"] = config_version
                
            evaluations = await self.evaluation_repo.find_many(filter_criteria)
            
            results = []
            for evaluation in evaluations:
                # Get response data for this evaluation
                evaluation_id = str(evaluation.id)
                
                # Get unique models from responses
                models_pipeline = [
                    {"$match": {"evaluation_id": evaluation_id}},
                    {"$group": {"_id": "$model_name", "count": {"$sum": 1}}}
                ]
                models_result = []
                async for model in self.database.responses.aggregate(models_pipeline):
                    models_result.append(model["_id"])
                
                # Get average scores (if any evaluation scores exist)
                scores_pipeline = [
                    {"$match": {"evaluation_id": ObjectId(evaluation_id)}},
                    {"$group": {
                        "_id": "$model_name",
                        "avg_score": {"$avg": "$overall_score"},
                        "detailed_scores": {"$first": "$detailed_scores"}
                    }}
                ]
                
                model_scores = {}
                async for score in self.database.evaluation_scores.aggregate(scores_pipeline):
                    model_scores[score["_id"]] = {
                        "overall": score["avg_score"],
                        "detailed": score["detailed_scores"]
                    }
                
                # Create result entries for each model
                for model_name in models_result:
                    result = {
                        "id": f"{evaluation_id}_{model_name}",
                        "model_name": model_name,
                        "evaluation_id": evaluation_id,
                        "config_version": evaluation.config_hash,
                        "timestamp": evaluation.completed_at or evaluation.started_at,
                        "status": evaluation.status,
                        "scores": model_scores.get(model_name, None)
                    }
                    results.append(result)
            
            # Sort by timestamp, newest first
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            return results
            
        except Exception as e:
            print(f"Error getting results: {e}")
            return []
    
    async def get_available_versions(self) -> List[str]:
        """Get list of available configuration versions."""
        try:
            versions = await self.evaluation_repo.collection.distinct("config_hash")
            return sorted(versions, reverse=True)
        except Exception as e:
            print(f"Error getting versions: {e}")
            return []
    
    async def get_detailed_result(self, model_name: str, config_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed results for a specific model."""
        try:
            # Find evaluation
            filter_criteria = {"status": "completed"}
            if config_version:
                filter_criteria["config_hash"] = config_version
                
            evaluation = await self.evaluation_repo.find_one(filter_criteria)
            if not evaluation:
                return None
                
            evaluation_id = str(evaluation.id)
            
            # Get all responses for this model in this evaluation
            responses = await self.response_repo.find_many({
                "evaluation_id": evaluation_id,
                "model_name": model_name
            })
            
            # Get evaluation scores
            scores_result = await self.database.evaluation_scores.find_one({
                "evaluation_id": ObjectId(evaluation_id),
                "model_name": model_name
            })
            
            # Format detailed result
            result = {
                "model_name": model_name,
                "evaluation_id": evaluation_id,
                "config_version": evaluation.config_hash,
                "timestamp": evaluation.completed_at or evaluation.started_at,
                "status": evaluation.status,
                "total_responses": len(responses),
                "responses": [
                    {
                        "sequence": resp.sequence,
                        "run": resp.run,
                        "prompt_name": resp.prompt_name,
                        "response": resp.response,
                        "generation_time": resp.generation_time,
                        "completed_at": resp.completed_at
                    }
                    for resp in responses
                ],
                "scores": {
                    "overall": scores_result["overall_score"] if scores_result else None,
                    "detailed": scores_result["detailed_scores"] if scores_result else {}
                } if scores_result else None
            }
            
            return result
            
        except Exception as e:
            print(f"Error getting detailed result: {e}")
            return None
