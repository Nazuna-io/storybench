"""Database-backed evaluation service replacing file-based progress tracking."""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models import Evaluation, Response, EvaluationStatus, ResponseStatus, GlobalSettings
from ..repositories import EvaluationRepository, ResponseRepository
from ..services.config_service import ConfigService

logger = logging.getLogger(__name__)

class DatabaseEvaluationRunner:
    """Database-backed evaluation runner with real-time progress tracking and caching."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """Initialize the evaluation runner."""
        self.database = database
        self.evaluation_repo = EvaluationRepository(database)
        self.response_repo = ResponseRepository(database)
        self.config_service = ConfigService(database)
        
        # Progress caching to reduce database queries during active evaluations
        self._progress_cache = {}
        self._batch_updates = []
        self._batch_update_threshold = 10  # Batch every 10 updates
        
    async def start_evaluation(self, 
                             models: List[str],
                             sequences: Dict[str, List[Dict[str, str]]],
                             criteria: Dict[str, Any],
                             global_settings: Dict[str, Any]) -> Evaluation:
        """Start a new evaluation with database tracking."""
        try:
            # Generate configuration hash for this evaluation
            config_data = {
                "models": models,
                "sequences": sequences,
                "criteria": criteria,
                "global_settings": global_settings
            }
            config_hash = self.config_service.generate_config_hash(config_data)
            
            # Calculate total tasks
            total_tasks = self._calculate_total_tasks(models, sequences, global_settings.get("num_runs", 3))
            
            # Create evaluation document
            evaluation = Evaluation(
                config_hash=config_hash,
                models=models,
                global_settings=GlobalSettings(**global_settings),
                total_tasks=total_tasks,
                status=EvaluationStatus.IN_PROGRESS
            )
            
            # Save to database
            evaluation = await self.evaluation_repo.create(evaluation)
            
            logger.info(f"Started evaluation {evaluation.id} with {total_tasks} total tasks")
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to start evaluation: {e}")
            raise
            
    def _calculate_total_tasks(self, models: List[str], sequences: Dict[str, List[Dict[str, str]]], num_runs: int) -> int:
        """Calculate the total number of tasks for this evaluation."""
        total_prompts = sum(len(prompts) for prompts in sequences.values())
        return len(models) * total_prompts * num_runs
        
    async def save_response(self, 
                          evaluation_id,  # Can be ObjectId or string
                          model_name: str,
                          sequence: str,
                          run: int,
                          prompt_index: int,
                          prompt_name: str,
                          prompt_text: str,
                          response_text: str,
                          generation_time: float) -> Response:
        """Save a model response to the database."""
        try:
            # Handle both ObjectId and string types
            if isinstance(evaluation_id, str):
                eval_id_obj = ObjectId(evaluation_id)
                eval_id_str = evaluation_id
            else:
                eval_id_obj = evaluation_id
                eval_id_str = str(evaluation_id)
            
            response = Response(
                evaluation_id=eval_id_str,  # Response model expects string
                model_name=model_name,
                sequence=sequence,
                run=run,
                prompt_index=prompt_index,
                prompt_name=prompt_name,
                prompt_text=prompt_text,
                response=response_text,
                generation_time=generation_time,
                status=ResponseStatus.COMPLETED
            )
            
            # Save to database
            response = await self.response_repo.create(response)
            
            # Update evaluation progress using ObjectId
            await self._update_evaluation_progress(eval_id_obj, model_name, sequence, run)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to save response: {e}")
            raise
        
    async def _update_evaluation_progress(self, evaluation_id: ObjectId, model_name: str, sequence: str, run: int):
        """Update evaluation progress with batching and caching."""
        try:
            eval_id_str = str(evaluation_id)
            
            # Update cache
            if eval_id_str not in self._progress_cache:
                self._progress_cache[eval_id_str] = 0
            self._progress_cache[eval_id_str] += 1
            
            # Add to batch updates
            self._batch_updates.append({
                "evaluation_id": evaluation_id,
                "model_name": model_name,
                "sequence": sequence,
                "run": run,
                "timestamp": datetime.utcnow()
            })
            
            # Flush batch if threshold reached
            if len(self._batch_updates) >= self._batch_update_threshold:
                await self._flush_batch_updates()
                
        except Exception as e:
            logger.error(f"Failed to update evaluation progress: {e}")
            
    async def _flush_batch_updates(self):
        """Flush batched progress updates to database."""
        if not self._batch_updates:
            return
            
        try:
            logger.debug(f"Flushing {len(self._batch_updates)} batched progress updates")
            
            # Group updates by evaluation_id and get latest for each
            latest_updates = {}
            for update in self._batch_updates:
                eval_id = str(update["evaluation_id"])
                if eval_id not in latest_updates or update["timestamp"] > latest_updates[eval_id]["timestamp"]:
                    latest_updates[eval_id] = update
            
            # Apply updates using cached counts instead of database queries
            for eval_id, update in latest_updates.items():
                completed_count = self._progress_cache.get(eval_id, 0)
                
                await self.evaluation_repo.update_progress(
                    update["evaluation_id"],
                    completed_count,
                    current_model=update["model_name"],
                    current_sequence=update["sequence"],
                    current_run=update["run"]
                )
            
            # Clear batch
            self._batch_updates.clear()
            logger.debug("Batch updates flushed successfully")
            
        except Exception as e:
            logger.error(f"Failed to flush batch updates: {e}")
            # Clear batch even on error to prevent accumulation
            self._batch_updates.clear()
            
    async def get_evaluation_progress(self, evaluation_id: ObjectId) -> Dict[str, Any]:
        """Get current progress using optimized statistics query."""
        try:
            evaluation = await self.evaluation_repo.find_by_id(evaluation_id)
            if not evaluation:
                return None
            
            # Use optimized statistics query instead of simple count
            stats = await self.response_repo.get_evaluation_statistics(evaluation_id)
            completed_count = stats["total_count"]
            
            # Update cache
            eval_id_str = str(evaluation_id)
            self._progress_cache[eval_id_str] = completed_count
            
            progress_percent = (completed_count / evaluation.total_tasks * 100) if evaluation.total_tasks > 0 else 0
            
            return {
                "evaluation_id": str(evaluation_id),
                "status": evaluation.status.value,
                "total_tasks": evaluation.total_tasks,
                "completed_tasks": completed_count,
                "progress_percent": round(progress_percent, 2),
                "current_model": evaluation.current_model,
                "current_sequence": evaluation.current_sequence,
                "current_run": evaluation.current_run,
                "started_at": evaluation.started_at,
                "completed_at": evaluation.completed_at,
                # Additional statistics from optimized query
                "model_count": stats["model_count"],
                "sequence_count": stats["sequence_count"],
                "avg_generation_time": stats["avg_generation_time"],
                "total_generation_time": stats["total_generation_time"],
                "by_model_count": stats["by_model_count"]
            }
                "started_at": evaluation.started_at.isoformat(),
                "completed_at": evaluation.completed_at.isoformat() if evaluation.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get evaluation progress: {e}")
            return None
            
    async def find_incomplete_evaluations(self) -> List[Evaluation]:
        """Find evaluations that can be resumed."""
        try:
            return await self.evaluation_repo.find_incomplete()
        except Exception as e:
            logger.error(f"Failed to find incomplete evaluations: {e}")
            return []
            
    async def mark_evaluation_completed(self, evaluation_id: ObjectId):
        """Mark an evaluation as completed."""
        try:
            await self.evaluation_repo.mark_completed(evaluation_id)
        except Exception as e:
            logger.error(f"Failed to mark evaluation completed: {e}")
            
    async def mark_evaluation_failed(self, evaluation_id: ObjectId, error_message: str):
        """Mark an evaluation as failed."""
        try:
            await self.evaluation_repo.mark_failed(evaluation_id, error_message)
        except Exception as e:
            logger.error(f"Failed to mark evaluation failed: {e}")
        
    async def get_resume_tasks(self, evaluation_id: ObjectId) -> List[Dict[str, Any]]:
        """Get list of incomplete tasks for resuming an evaluation."""
        try:
            evaluation = await self.evaluation_repo.find_by_id(evaluation_id)
            if not evaluation:
                return []
                
            # Get completed tasks
            completed_tasks = await self.response_repo.find_incomplete_for_evaluation(evaluation_id)
            
            # Generate all possible tasks for this evaluation
            # This would need access to the original sequences and settings
            # For now, return completed task info
            
            return completed_tasks
            
        except Exception as e:
            logger.error(f"Failed to get resume tasks: {e}")
            return []
            
    async def resume_evaluation(self, evaluation_id: ObjectId) -> bool:
        """Resume an incomplete evaluation."""
        try:
            evaluation = await self.evaluation_repo.find_by_id(evaluation_id)
            if not evaluation:
                return False
                
            if evaluation.status != EvaluationStatus.PAUSED:
                # Mark as in progress for resume
                await self.evaluation_repo.update_by_id(
                    evaluation_id, 
                    {"status": EvaluationStatus.IN_PROGRESS.value}
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume evaluation: {e}")
            return False
            
    async def pause_evaluation(self, evaluation_id: ObjectId) -> bool:
        """Pause an evaluation."""
        try:
            await self.evaluation_repo.update_by_id(
                evaluation_id,
                {"status": EvaluationStatus.PAUSED.value}
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause evaluation: {e}")
            return False
            
    async def find_running_evaluations(self) -> List[Evaluation]:
        """Find currently running evaluations."""
        try:
            # Include all statuses that represent an evaluation in progress
            running_statuses = [
                EvaluationStatus.IN_PROGRESS,
                EvaluationStatus.GENERATING_RESPONSES,
                EvaluationStatus.RESPONSES_COMPLETE,
                EvaluationStatus.EVALUATING_RESPONSES
            ]
            
            running_evaluations = []
            for status in running_statuses:
                evals = await self.evaluation_repo.find_by_status(status)
                running_evaluations.extend(evals)
            
            return running_evaluations
        except Exception as e:
            logger.error(f"Failed to find running evaluations: {e}")
            return []
            
    async def finalize_evaluation(self, evaluation_id: ObjectId) -> bool:
        """Finalize evaluation and flush any remaining updates."""
        try:
            # Flush any remaining batch updates
            await self._flush_batch_updates()
            
            # Clear cache for this evaluation
            eval_id_str = str(evaluation_id)
            if eval_id_str in self._progress_cache:
                del self._progress_cache[eval_id_str]
            
            # Update evaluation status to completed
            await self.evaluation_repo.update_status(evaluation_id, EvaluationStatus.COMPLETED)
            
            logger.info(f"Evaluation {evaluation_id} finalized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to finalize evaluation {evaluation_id}: {e}")
            return False
            
    import traceback
    from datetime import datetime

    async def stop_evaluation(self, evaluation_id: ObjectId) -> bool:
        """Stop a running evaluation."""
        try:
            now = datetime.utcnow().isoformat()
            stack = ''.join(traceback.format_stack(limit=10))
            logger.warning(f"[DEBUG] stop_evaluation called at {now} for evaluation_id={evaluation_id}\nStack trace:\n{stack}")
            await self.evaluation_repo.update_by_id(
                evaluation_id,
                {"status": EvaluationStatus.STOPPED.value}
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop evaluation: {e}")
            return False
