"""
Sequence worker implementation for parallel evaluation execution.

Each worker handles one sequence (5 sequences: FilmNarrative, LiteraryNarrative, 
CommercialConcept, RegionalThriller, CrossGenre) with proper context accumulation
within runs and isolation between runs.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass 
class SequenceWorkerState:
    """State tracking for individual sequence worker."""
    sequence_name: str
    model_name: str
    worker_id: str
    run_number: int
    current_prompt_index: int = 0
    context_history: List[Dict[str, str]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error_count: int = 0
    completed_prompts: int = 0
    total_prompts: int = 3  # Always 3 prompts per sequence
    status: str = "initialized"  # initialized, running, completed, failed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/monitoring."""
        return {
            "sequence_name": self.sequence_name,
            "model_name": self.model_name,
            "worker_id": self.worker_id,
            "run_number": self.run_number,
            "current_prompt_index": self.current_prompt_index,
            "completed_prompts": self.completed_prompts,
            "total_prompts": self.total_prompts,
            "error_count": self.error_count,
            "status": self.status,
            "context_length": len(self.context_history),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


class SequenceWorker:
    """
    Individual worker responsible for executing one sequence with all its runs.
    
    Handles:
    - 1 sequence (e.g., FilmNarrative) 
    - 3 prompts per sequence
    - 3 runs per sequence (for variance checking)
    - Context accumulation within each run
    - Context reset between runs
    """
    
    def __init__(self, 
                 worker_id: str,
                 sequence_name: str, 
                 sequence_prompts: List[Dict[str, str]],  # 3 prompts
                 model_name: str,
                 model_config: Dict[str, Any],
                 num_runs: int,  # typically 3
                 evaluator_factory: Callable,
                 evaluation_runner,
                 evaluation_id: str,
                 rate_limit_manager):
        
        self.worker_id = worker_id
        self.sequence_name = sequence_name
        self.sequence_prompts = sequence_prompts
        self.model_name = model_name
        self.model_config = model_config
        self.num_runs = num_runs
        self.evaluator_factory = evaluator_factory
        self.evaluation_runner = evaluation_runner
        self.evaluation_id = evaluation_id
        self.rate_limit_manager = rate_limit_manager
        
        # Extract provider from model configuration
        self.provider = self._determine_provider(model_config)
        
        # Initialize states for each run (3 runs for variance checking)
        self.run_states = []
        for run_num in range(1, num_runs + 1):
            state = SequenceWorkerState(
                sequence_name=sequence_name,
                model_name=model_name,
                worker_id=f"{worker_id}_run_{run_num}",
                run_number=run_num,
                total_prompts=len(sequence_prompts)  # Should be 3
            )
            self.run_states.append(state)
    
    def _determine_provider(self, model_config: Dict[str, Any]) -> str:
        """Determine provider from model configuration."""
        model_id = model_config.get("model_id", "")
        
        if "claude" in model_id.lower():
            return "anthropic"
        elif "gpt" in model_id.lower() or "o4" in model_id.lower():
            return "openai"
        elif "gemini" in model_id.lower():
            return "google"
        elif any(x in model_id.lower() for x in ["deepseek", "qwen", "llama", "meta-"]):
            return "deepinfra"
        else:
            return "local"
    
    async def execute(self) -> Dict[str, Any]:
        """Execute all runs for this sequence."""
        logger.info(f"Worker {self.worker_id} starting: {self.model_name} - {self.sequence_name}")
        
        results = {
            "worker_id": self.worker_id,
            "sequence_name": self.sequence_name,
            "model_name": self.model_name,
            "provider": self.provider,
            "total_runs": self.num_runs,
            "completed_runs": 0,
            "failed_runs": 0,
            "total_prompts": len(self.sequence_prompts) * self.num_runs,  # 3 prompts × 3 runs = 9
            "completed_prompts": 0,
            "start_time": datetime.utcnow(),
            "run_results": []
        }
        
        try:
            # Execute each run sequentially (context must reset between runs)
            for run_state in self.run_states:
                run_result = await self._execute_run(run_state)
                results["run_results"].append(run_result)
                
                if run_result["success"]:
                    results["completed_runs"] += 1
                    results["completed_prompts"] += run_result["completed_prompts"]
                else:
                    results["failed_runs"] += 1
                    logger.warning(f"Run {run_state.run_number} failed for {self.worker_id}")
            
            results["end_time"] = datetime.utcnow()
            results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
            results["success"] = results["completed_runs"] > 0
            
            logger.info(f"Worker {self.worker_id} completed: {results['completed_runs']}/{results['total_runs']} runs successful")
            return results
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} failed with exception: {e}")
            results["error"] = str(e)
            results["success"] = False
            return results    
    async def _execute_run(self, run_state: SequenceWorkerState) -> Dict[str, Any]:
        """Execute a single run (all 3 prompts in sequence with context accumulation)."""
        run_state.status = "running"
        run_state.start_time = datetime.utcnow()
        
        run_result = {
            "run_number": run_state.run_number,
            "worker_id": run_state.worker_id,
            "completed_prompts": 0,
            "success": False,
            "error": None,
            "prompt_results": []
        }
        
        try:
            # Create evaluator instance for this run
            evaluator = self.evaluator_factory(self.model_config)
            
            # IMPORTANT: Setup the evaluator before use
            await evaluator.setup()
            
            # Execute 3 prompts in sequence with context accumulation
            for prompt_index, prompt in enumerate(self.sequence_prompts):
                run_state.current_prompt_index = prompt_index
                run_state.last_activity = datetime.utcnow()
                
                try:
                    # Build context from previous responses in this run
                    context_text = self._build_context_text(run_state.context_history)
                    
                    # Acquire rate limit permission
                    success = await self.rate_limit_manager.acquire(self.provider)
                    if not success:
                        raise Exception(f"Rate limit acquisition failed for {self.provider}")
                    
                    try:
                        # Execute prompt with context
                        prompt_text_with_context = f"{context_text}\n\n{prompt['text']}" if context_text else prompt['text']
                        
                        response_dict = await evaluator.generate_response(
                            prompt_text_with_context
                        )
                        
                        # Extract response text and generation time from dict
                        response_text = response_dict.get("response", "")
                        generation_time = response_dict.get("generation_time", 0.0)
                        
                        # Record success for circuit breaker
                        self.rate_limit_manager.record_success(self.provider)
                        
                        # Save response to database
                        await self.evaluation_runner.save_response(
                            evaluation_id=self.evaluation_id,
                            model_name=self.model_name,
                            sequence=self.sequence_name,
                            run=run_state.run_number,
                            prompt_index=prompt_index,
                            prompt_name=prompt["name"],
                            prompt_text=prompt["text"],
                            response_text=response_text,
                            generation_time=generation_time
                        )
                        
                        # Add to context history for next prompt in this run
                        run_state.context_history.append({
                            "prompt": prompt["text"],
                            "response": response_text,
                            "prompt_name": prompt["name"]
                        })
                        
                        run_state.completed_prompts += 1
                        run_result["completed_prompts"] += 1
                        
                        run_result["prompt_results"].append({
                            "prompt_index": prompt_index,
                            "prompt_name": prompt["name"],
                            "success": True,
                            "generation_time": generation_time,
                            "response_length": len(response_text)
                        })
                        
                        logger.debug(f"Worker {run_state.worker_id} completed prompt {prompt_index + 1}/3")
                        
                    except Exception as api_error:
                        # Record error for circuit breaker
                        self.rate_limit_manager.record_error(self.provider)
                        raise api_error
                        
                    finally:
                        # Always release rate limit
                        self.rate_limit_manager.release(self.provider)
                        
                except Exception as prompt_error:
                    logger.error(f"Worker {run_state.worker_id} failed on prompt {prompt_index}: {prompt_error}")
                    run_state.error_count += 1
                    
                    run_result["prompt_results"].append({
                        "prompt_index": prompt_index,
                        "prompt_name": prompt["name"],
                        "success": False,
                        "error": str(prompt_error)
                    })
                    
                    # Continue with next prompt instead of failing entire run
                    continue
            
            # Mark run as successful if at least one prompt completed
            run_result["success"] = run_result["completed_prompts"] > 0
            run_state.status = "completed" if run_result["success"] else "failed"
            
            # IMPORTANT: Reset context between runs (for variance checking)
            run_state.context_history.clear()
            
            return run_result
            
        except Exception as e:
            logger.error(f"Run {run_state.run_number} failed for worker {run_state.worker_id}: {e}")
            run_result["error"] = str(e)
            run_state.status = "failed"
            return run_result
    
    def _build_context_text(self, context_history: List[Dict[str, str]]) -> str:
        """Build accumulated context text from previous responses."""
        if not context_history:
            return ""
        
        context_parts = []
        for i, entry in enumerate(context_history):
            context_parts.append(f"### Previous Response {i+1} ({entry['prompt_name']}):\n{entry['response']}")
        
        return "\n\n".join(context_parts)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state for monitoring."""
        return {
            "worker_id": self.worker_id,
            "sequence_name": self.sequence_name,
            "model_name": self.model_name,
            "provider": self.provider,
            "run_states": [state.to_dict() for state in self.run_states]
        }
