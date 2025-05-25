"""Evaluation service for background processing and progress tracking."""

import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime

from ...models.config import Config
from ...models.progress import ProgressTracker
from ...evaluators.factory import EvaluatorFactory
from ..models.responses import EvaluationStatus, ProgressInfo, ResumeInfo


class EvaluationService:
    """Service for managing background evaluation execution."""
    
    def __init__(self):
        """Initialize evaluation service."""
        self._current_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._current_model: Optional[str] = None
        self._progress_callback: Optional[Callable] = None
        self._output_callback: Optional[Callable] = None
        self._error_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        
        # Progress tracking
        self._total_tasks = 0
        self._completed_tasks = 0
        self._current_sequence = ""
        self._current_run = 0
        self._current_prompt = ""        
    def set_callbacks(self, 
                     progress_callback: Optional[Callable] = None,
                     output_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None):
        """Set callbacks for real-time updates."""
        self._progress_callback = progress_callback
        self._output_callback = output_callback  
        self._error_callback = error_callback
        
    async def start_evaluation(self, config: Config, api_keys: Dict[str, str], 
                             resume: bool = False) -> bool:
        """Start background evaluation process."""
        with self._lock:
            if self._is_running:
                return False
                
            self._is_running = True
            self._current_model = None
            
        try:
            # Calculate total tasks for progress tracking
            await self._calculate_total_tasks(config)
            
            # Start background task
            self._current_task = asyncio.create_task(
                self._run_evaluation_background(config, api_keys, resume)
            )
            
            return True
            
        except Exception as e:
            self._is_running = False
            if self._error_callback:
                self._error_callback(f"Failed to start evaluation: {str(e)}")
            return False
            
    async def stop_evaluation(self) -> bool:
        """Stop running evaluation."""
        with self._lock:
            if not self._is_running or not self._current_task:
                return False
                
            self._current_task.cancel()
            self._is_running = False
            self._current_model = None
            
        if self._output_callback:
            self._output_callback("🛑 Evaluation stopped by user")
            
        return True        
    def get_status(self) -> Dict[str, Any]:
        """Get current evaluation status."""
        with self._lock:
            return {
                "running": self._is_running,
                "current_model": self._current_model,
                "progress": {
                    "total_tasks": self._total_tasks,
                    "completed_tasks": self._completed_tasks,
                    "current_sequence": self._current_sequence,
                    "current_run": self._current_run,
                    "current_prompt": self._current_prompt,
                    "progress_percentage": (
                        (self._completed_tasks / self._total_tasks * 100) 
                        if self._total_tasks > 0 else 0
                    )
                }
            }
            
    async def get_resume_status(self, config: Config) -> ResumeInfo:
        """Check resume status for current configuration."""
        tracker = ProgressTracker()
        config_hash = config.get_version_hash()
        
        sequences = list(config.prompts.keys())
        prompts_per_sequence = {seq: len(prompts) for seq, prompts in config.prompts.items()}
        
        models_completed = []
        models_in_progress = []
        models_pending = []
        
        for model in config.models:
            if model.type != 'api':  # Skip local models for now
                continue
                
            is_complete = tracker.is_complete(
                model.name, config_hash, sequences,
                config.global_settings.num_runs, prompts_per_sequence
            )
            
            if is_complete:
                models_completed.append(model.name)
            else:
                # Check if any work has been done
                next_task = tracker.get_next_task(
                    model.name, config_hash, sequences,
                    config.global_settings.num_runs, prompts_per_sequence
                )
                
                if next_task and (next_task[1] > 1 or next_task[2] > 0 or next_task[3] > 0):
                    models_in_progress.append(model.name)
                else:
                    models_pending.append(model.name)
                    
        can_resume = len(models_in_progress) > 0
        
        return ResumeInfo(
            can_resume=can_resume,
            models_completed=models_completed,
            models_in_progress=models_in_progress,
            models_pending=models_pending
        )        
    async def _calculate_total_tasks(self, config: Config):
        """Calculate total number of tasks for progress tracking."""
        total = 0
        for model in config.models:
            if model.type != 'api':  # Skip local models
                continue
                
            for sequence, prompts in config.prompts.items():
                total += len(prompts) * config.global_settings.num_runs
                
        self._total_tasks = total
        self._completed_tasks = 0
        
    async def _run_evaluation_background(self, config: Config, api_keys: Dict[str, str], resume: bool):
        """Run evaluation in background task."""
        try:
            if self._output_callback:
                self._output_callback("🚀 Starting evaluation...")
                
            tracker = ProgressTracker()
            config_hash = config.get_version_hash()
            
            # Calculate sequences and prompts
            sequences = list(config.prompts.keys())
            prompts_per_sequence = {seq: len(prompts) for seq, prompts in config.prompts.items()}
            
            for model in config.models:
                if model.type != 'api':  # Skip local models for now
                    if self._output_callback:
                        self._output_callback(f"⏭️  Skipping {model.name} - local models not yet implemented")
                    continue
                    
                with self._lock:
                    self._current_model = model.name
                    
                if self._output_callback:
                    self._output_callback(f"🔄 Processing {model.name}...")
                    
                # Check if already complete
                if tracker.is_complete(model.name, config_hash, sequences,
                                     config.global_settings.num_runs, prompts_per_sequence):
                    if self._output_callback:
                        self._output_callback(f"✅ {model.name} already complete")
                    continue
                    
                # Create evaluator
                try:
                    evaluator = EvaluatorFactory.create_evaluator(model.name, model.__dict__, api_keys)
                except Exception as e:
                    if self._error_callback:
                        self._error_callback(f"Failed to create evaluator for {model.name}: {str(e)}")
                    continue
                    
                # Setup evaluator
                if not await evaluator.setup():
                    if self._error_callback:
                        self._error_callback(f"Failed to setup {model.name}")
                    continue                    
                try:
                    await self._process_model(evaluator, config, tracker, config_hash,
                                            sequences, prompts_per_sequence)
                finally:
                    await evaluator.cleanup()
                    
            if self._output_callback:
                self._output_callback("🎉 Evaluation complete!")
                
        except asyncio.CancelledError:
            if self._output_callback:
                self._output_callback("⏹️  Evaluation cancelled")
        except Exception as e:
            if self._error_callback:
                self._error_callback(f"Evaluation failed: {str(e)}")
        finally:
            with self._lock:
                self._is_running = False
                self._current_model = None                
    async def _process_model(self, evaluator, config, tracker, config_hash, sequences, prompts_per_sequence):
        """Process all tasks for a single model."""
        model_name = evaluator.name
        
        # Get next task to resume from
        next_task = tracker.get_next_task(
            model_name, config_hash, sequences,
            config.global_settings.num_runs, prompts_per_sequence
        )
        
        if not next_task:
            if self._output_callback:
                self._output_callback(f"✅ {model_name} - no tasks remaining")
            return
            
        start_sequence_idx, start_run, start_prompt_idx, tasks_done = next_task
        
        # Update completed tasks counter
        with self._lock:
            self._completed_tasks += tasks_done
        
        # Process sequences
        for seq_idx, sequence in enumerate(sequences[start_sequence_idx:], start_sequence_idx):
            prompts = config.prompts[sequence]
            
            with self._lock:
                self._current_sequence = sequence
                
            for run in range(start_run if seq_idx == start_sequence_idx else 1, 
                           config.global_settings.num_runs + 1):
                with self._lock:
                    self._current_run = run
                    
                start_prompt = start_prompt_idx if (seq_idx == start_sequence_idx and run == start_run) else 0
                
                for prompt_idx, (prompt_name, prompt_text) in enumerate(prompts.items()):
                    if prompt_idx < start_prompt:
                        continue
                        
                    with self._lock:
                        self._current_prompt = prompt_name
                        
                    if self._output_callback:
                        self._output_callback(f"📝 {model_name} | {sequence} | Run {run} | {prompt_name}")
                        
                    try:
                        # Execute prompt
                        response = await evaluator.evaluate(prompt_text)
                        
                        # Save result
                        tracker.save_response(
                            model_name, config_hash, sequence, run, prompt_idx, prompt_name, response
                        )
                        
                        # Update progress
                        with self._lock:
                            self._completed_tasks += 1
                            
                        if self._progress_callback:
                            self._progress_callback(self.get_status())
                            
                    except Exception as e:
                        if self._error_callback:
                            self._error_callback(f"Error processing {prompt_name}: {str(e)}")
                        continue