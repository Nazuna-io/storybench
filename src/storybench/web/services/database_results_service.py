"""Database-based results service for evaluation data."""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ...database.repositories.evaluation_repo import EvaluationRepository
from ...database.repositories.response_repo import ResponseRepository


class DatabaseResultsService:
    """Service for retrieving evaluation results from database."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.evaluation_repo = EvaluationRepository(database)
        self.response_repo = ResponseRepository(database)
        
    def _map_status_to_display(self, internal_status: str) -> str:
        """Map internal status to user-friendly display status."""
        status_mapping = {
            "in_progress": "prompting",
            "generating_responses": "prompting", 
            "responses_complete": "evaluating",
            "evaluating_responses": "evaluating",
            "completed": "completed",
            "failed": "failed",
            "stopped": "stopped",
            "paused": "stopped"
        }
        return status_mapping.get(internal_status, internal_status)
        
    async def get_all_results(self, config_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all evaluation results with optional filtering."""
        try:
            # Get all evaluations (including in-progress and completed ones)
            filter_criteria = {}
            if config_version:
                filter_criteria["config_hash"] = config_version
                
            evaluations = await self.evaluation_repo.find_many(filter_criteria)
            
            results = []
            for evaluation in evaluations:
                evaluation_id = str(evaluation.id)
                
                # Get unique models from evaluation.models (for in-progress) or responses (for completed)
                models_from_eval = evaluation.models or []
                models_from_responses = []
                
                # Also get models from responses if they exist
                models_pipeline = [
                    {"$match": {"evaluation_id": evaluation_id}},
                    {"$group": {"_id": "$model_name", "count": {"$sum": 1}}}
                ]
                async for model in self.database.responses.aggregate(models_pipeline):
                    models_from_responses.append(model["_id"])
                
                # Use models from responses if available, otherwise from evaluation
                models_result = models_from_responses if models_from_responses else models_from_eval
                
                # Get scores from response_llm_evaluations collection
                model_scores = {}
                for model_name in models_result:
                    # Get all response IDs for this model and evaluation
                    responses = await self.database.responses.find({
                        "evaluation_id": evaluation_id,
                        "model_name": model_name
                    }).to_list(None)
                    
                    if responses:
                        response_ids = [resp["_id"] for resp in responses]
                        
                        # Get LLM evaluations for these responses
                        llm_evaluations = await self.database.response_llm_evaluations.find({
                            "response_id": {"$in": response_ids}
                        }).to_list(None)
                        
                        if llm_evaluations:
                            # Calculate average scores across all criteria and evaluations
                            all_scores = []
                            criteria_scores = {}
                            
                            for llm_eval in llm_evaluations:
                                for criterion in llm_eval.get("criteria_results", []):
                                    criterion_name = criterion.get("criterion_name")
                                    score = criterion.get("score")
                                    if criterion_name and score is not None:
                                        if criterion_name not in criteria_scores:
                                            criteria_scores[criterion_name] = []
                                        criteria_scores[criterion_name].append(score)
                                        all_scores.append(score)
                            
                            # Calculate averages
                            overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
                            detailed_avg = {
                                criterion: sum(scores) / len(scores)
                                for criterion, scores in criteria_scores.items()
                            }
                            
                            model_scores[model_name] = {
                                "overall": round(overall_avg, 2),
                                "detailed": detailed_avg,
                                "total_evaluations": len(llm_evaluations),
                                "total_responses": len(responses)
                            }
                        else:
                            # No LLM evaluations yet, but responses exist
                            model_scores[model_name] = {
                                "overall": None,
                                "detailed": {},
                                "total_evaluations": 0,
                                "total_responses": len(responses)
                            }
                
                # Create result entries for each model
                for model_name in models_result:
                    # Map status to user-friendly display
                    display_status = self._map_status_to_display(evaluation.status)
                    
                    # Calculate progress percent based on status
                    if evaluation.status == "completed":
                        progress_percent = 100.0
                    elif hasattr(evaluation, 'completed_tasks') and evaluation.completed_tasks:
                        progress_percent = round((evaluation.completed_tasks / evaluation.total_tasks * 100) if evaluation.total_tasks > 0 else 0, 1)
                    else:
                        # Count actual responses for this evaluation
                        response_count = await self.response_repo.count_by_evaluation_id(evaluation.id)
                        progress_percent = round((response_count / evaluation.total_tasks * 100) if evaluation.total_tasks > 0 else 0, 1)
                    
                    result = {
                        "id": f"{evaluation_id}_{model_name}",
                        "model_name": model_name,
                        "evaluation_id": evaluation_id,
                        "config_version": evaluation.config_hash,
                        "timestamp": evaluation.completed_at or evaluation.started_at,
                        "status": display_status,
                        "internal_status": evaluation.status,  # Keep for debugging
                        "scores": model_scores.get(model_name, None),
                        "total_tasks": evaluation.total_tasks,
                        "completed_tasks": evaluation.completed_tasks,
                        "progress_percent": progress_percent,
                        "current_model": getattr(evaluation, 'current_model', None),
                        "current_sequence": getattr(evaluation, 'current_sequence', None),
                        "current_run": getattr(evaluation, 'current_run', None)
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
            # Find evaluation (not just completed ones)
            filter_criteria = {}
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
            
            # Get LLM evaluations for these responses
            response_ids = [resp.id for resp in responses]
            llm_evaluations = await self.database.response_llm_evaluations.find({
                "response_id": {"$in": response_ids}
            }).to_list(None)
            
            # Calculate scores from LLM evaluations
            scores_data = None
            if llm_evaluations:
                all_scores = []
                criteria_scores = {}
                
                for llm_eval in llm_evaluations:
                    for criterion in llm_eval.get("criteria_results", []):
                        criterion_name = criterion.get("criterion_name")
                        score = criterion.get("score")
                        if criterion_name and score is not None:
                            if criterion_name not in criteria_scores:
                                criteria_scores[criterion_name] = []
                            criteria_scores[criterion_name].append(score)
                            all_scores.append(score)
                
                overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
                detailed_avg = {
                    criterion: sum(scores) / len(scores)
                    for criterion, scores in criteria_scores.items()
                }
                
                scores_data = {
                    "overall": round(overall_avg, 2),
                    "detailed": detailed_avg
                }
            
            # Format detailed result
            result = {
                "model_name": model_name,
                "evaluation_id": evaluation_id,
                "config_version": evaluation.config_hash,
                "timestamp": evaluation.completed_at or evaluation.started_at,
                "status": evaluation.status,
                "total_responses": len(responses),
                "total_evaluations": len(llm_evaluations),
                "responses": [
                    {
                        "id": str(resp.id),
                        "sequence": resp.sequence,
                        "run": resp.run,
                        "prompt_name": resp.prompt_name,
                        "response": resp.response,
                        "generation_time": resp.generation_time,
                        "completed_at": resp.completed_at
                    }
                    for resp in responses
                ],
                "scores": scores_data
            }
            
            return result
            
        except Exception as e:
            print(f"Error getting detailed result: {e}")
            return None
