"""
Main parallel evaluation runner orchestrating sequence workers.

Coordinates execution of:
- 5 sequences (FilmNarrative, LiteraryNarrative, CommercialConcept, RegionalThriller, CrossGenre)
- 12+ models (scaling to 50+)
- 3 runs per sequence for variance checking
- 3 prompts per run with context accumulation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from .sequence_workers import SequenceWorker
from .rate_limiting import RateLimitManager
from .progress_tracking import ParallelEvaluationProgress, ProgressReporter

logger = logging.getLogger(__name__)


class ParallelSequenceEvaluationRunner:
    """Main orchestrator for parallel sequence evaluation."""
    
    def __init__(self, 
                 database,
                 evaluation_runner,
                 max_concurrent_sequences: Optional[int] = None):
        
        self.database = database
        self.evaluation_runner = evaluation_runner
        self.rate_limit_manager = RateLimitManager()
        
        # Conservative concurrency for 5 sequences - can be tuned up
        # Start with 5 (one per sequence) for safety
        self.max_concurrent_sequences = max_concurrent_sequences or 5
        self.progress = ParallelEvaluationProgress()
        
        # Worker management
        self.active_workers = {}
        self.worker_tasks = {}
        
    async def run_parallel_evaluation(self,
                                    evaluation_id: str,
                                    models: List[Dict[str, Any]],  # 12+ models
                                    sequences: Dict[str, List[Dict[str, str]]],  # 5 sequences
                                    num_runs: int,  # 3 runs
                                    evaluator_factory: Callable,
                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run evaluation with parallel sequence execution.
        
        Total scale: 12 models × 5 sequences × 3 prompts × 3 runs = 540 API calls
        Expected speedup: 5x (5 sequences in parallel) per model
        """
        
        logger.info(f"Starting parallel evaluation {evaluation_id}")
        logger.info(f"Scale: {len(models)} models × {len(sequences)} sequences × 3 prompts × {num_runs} runs = {len(models) * len(sequences) * 3 * num_runs} total API calls")
        logger.info(f"Max concurrent sequences: {self.max_concurrent_sequences}")
        
        self.progress.start_time = datetime.utcnow()
        
        # Calculate total work
        total_prompts_per_model = len(sequences) * 3 * num_runs  # 5 sequences × 3 prompts × 3 runs = 45
        self.progress.total_prompts = len(models) * total_prompts_per_model
        
        # Initialize progress reporter
        progress_reporter = ProgressReporter(self.progress, log_interval=30, detailed_logging=True)
        
        results = {
            "evaluation_id": evaluation_id,
            "start_time": self.progress.start_time,
            "models": len(models),
            "sequences": len(sequences),
            "runs_per_sequence": num_runs,
            "total_workers": 0,
            "successful_workers": 0,
            "failed_workers": 0,
            "model_results": {},
            "provider_stats": {},
            "performance_metrics": {}
        }
        
        try:
            # Process each model with parallel sequences
            for model_index, model_config in enumerate(models):
                model_name = model_config["name"]
                logger.info(f"Starting parallel sequences for model {model_index + 1}/{len(models)}: {model_name}")
                
                model_result = await self._run_model_sequences_parallel(
                    evaluation_id=evaluation_id,
                    model_config=model_config,
                    sequences=sequences,
                    num_runs=num_runs,
                    evaluator_factory=evaluator_factory,
                    progress_reporter=progress_reporter
                )
                
                results["model_results"][model_name] = model_result
                results["total_workers"] += model_result["total_workers"]
                results["successful_workers"] += model_result["successful_workers"]
                results["failed_workers"] += model_result["failed_workers"]
                
                # Update progress
                self.progress.completed_prompts += model_result.get("completed_prompts", 0)
                progress_reporter.log_progress()
            
            # Final statistics
            results["end_time"] = datetime.utcnow()
            results["total_duration"] = (results["end_time"] - results["start_time"]).total_seconds()
            results["provider_stats"] = self.rate_limit_manager.get_all_provider_stats()
            results["performance_metrics"] = self._calculate_performance_metrics(results)
            results["success"] = results["successful_workers"] > 0
            
            # Final summary
            progress_reporter.log_final_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel evaluation failed: {e}")
            results["error"] = str(e)
            results["success"] = False
            return results    
    async def _run_model_sequences_parallel(self,
                                          evaluation_id: str,
                                          model_config: Dict[str, Any],
                                          sequences: Dict[str, List[Dict[str, str]]],
                                          num_runs: int,
                                          evaluator_factory: Callable,
                                          progress_reporter) -> Dict[str, Any]:
        """Run all 5 sequences for a single model in parallel."""
        
        model_name = model_config["name"]
        
        # Create workers for all 5 sequences
        workers = []
        for sequence_name, sequence_prompts in sequences.items():
            worker_id = f"{model_name}_{sequence_name}"
            
            worker = SequenceWorker(
                worker_id=worker_id,
                sequence_name=sequence_name,
                sequence_prompts=sequence_prompts,  # 3 prompts
                model_name=model_name,
                model_config=model_config,
                num_runs=num_runs,  # 3 runs
                evaluator_factory=evaluator_factory,
                evaluation_runner=self.evaluation_runner,
                evaluation_id=evaluation_id,
                rate_limit_manager=self.rate_limit_manager
            )
            workers.append(worker)
        
        # Execute workers with concurrency limit (max 5 for 5 sequences)
        semaphore = asyncio.Semaphore(self.max_concurrent_sequences)
        
        async def execute_worker_with_limit(worker):
            async with semaphore:
                return await worker.execute()
        
        # Start all 5 sequence workers
        logger.info(f"Starting {len(workers)} sequence workers for {model_name}")
        
        try:
            # Execute all sequences concurrently
            worker_results = await asyncio.gather(
                *[execute_worker_with_limit(worker) for worker in workers],
                return_exceptions=True
            )
            
            # Process results
            model_result = {
                "model_name": model_name,
                "total_workers": len(workers),
                "successful_workers": 0,
                "failed_workers": 0,
                "completed_prompts": 0,
                "worker_results": []
            }
            
            for i, result in enumerate(worker_results):
                if isinstance(result, Exception):
                    logger.error(f"Worker {workers[i].worker_id} raised exception: {result}")
                    model_result["failed_workers"] += 1
                    model_result["worker_results"].append({
                        "worker_id": workers[i].worker_id,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    if result.get("success", False):
                        model_result["successful_workers"] += 1
                    else:
                        model_result["failed_workers"] += 1
                    
                    model_result["completed_prompts"] += result.get("completed_prompts", 0)
                    model_result["worker_results"].append(result)
            
            logger.info(f"Model {model_name} completed: {model_result['successful_workers']}/{model_result['total_workers']} workers successful")
            return model_result
            
        except Exception as e:
            logger.error(f"Failed to execute workers for model {model_name}: {e}")
            return {
                "model_name": model_name,
                "total_workers": len(workers),
                "successful_workers": 0,
                "failed_workers": len(workers),
                "completed_prompts": 0,
                "error": str(e)
            }
    
    def _calculate_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for the evaluation."""
        duration_minutes = results.get("total_duration", 0) / 60
        total_prompts = self.progress.total_prompts
        completed_prompts = self.progress.completed_prompts
        
        metrics = {
            "duration_minutes": duration_minutes,
            "total_prompts": total_prompts,
            "completed_prompts": completed_prompts,
            "success_rate": (completed_prompts / total_prompts * 100) if total_prompts > 0 else 0,
            "average_throughput_per_minute": completed_prompts / duration_minutes if duration_minutes > 0 else 0,
            "estimated_sequential_time": total_prompts * 0.5,  # Assume 30s per prompt sequentially
            "parallelization_speedup": 0
        }
        
        # Calculate estimated speedup
        if duration_minutes > 0:
            sequential_duration = metrics["estimated_sequential_time"]
            metrics["parallelization_speedup"] = sequential_duration / duration_minutes
        
        return metrics
    
    async def get_real_time_progress(self) -> Dict[str, Any]:
        """Get current progress for monitoring dashboards."""
        provider_stats = self.rate_limit_manager.get_all_provider_stats()
        self.progress.provider_stats = provider_stats
        
        return self.progress.to_dict()
