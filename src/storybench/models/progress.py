"""Progress tracking and resume functionality."""

import json
import os
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime


class ProgressTracker:
    """Tracks progress and enables resume functionality."""
    
    def __init__(self, results_dir: str = "output"):
        """Initialize progress tracker."""
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def get_result_file_path(self, model_name: str, config_hash: str) -> Path:
        """Get the path for a model's result file."""
        safe_name = model_name.replace("/", "_").replace(" ", "_")
        filename = f"{safe_name}_{config_hash}.json"
        return self.results_dir / filename
        
    def save_response(self, model_name: str, config_hash: str, sequence: str, 
                     run: int, prompt_idx: int, prompt_name: str,
                     response_data: Dict[str, Any]) -> None:
        """Save a single response to the results file."""
        file_path = self.get_result_file_path(model_name, config_hash)
        
        # Load existing data or create new structure
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = self._create_empty_result_structure(model_name)
            
        # Ensure sequence and run exist
        if sequence not in data["sequences"]:
            data["sequences"][sequence] = {}
        run_key = f"run_{run}"
        if run_key not in data["sequences"][sequence]:
            data["sequences"][sequence][run_key] = []            
        # Add the response
        response_entry = {
            "prompt_name": prompt_name,
            "prompt_text": response_data.get("prompt_text", ""),
            "response": response_data["response"],
            "generation_time": response_data["generation_time"],
            "completed_at": response_data["completed_at"]
        }
        
        # Insert at correct index or append
        run_responses = data["sequences"][sequence][run_key]
        while len(run_responses) <= prompt_idx:
            run_responses.append(None)
        run_responses[prompt_idx] = response_entry
        
        # Update metadata
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def is_complete(self, model_name: str, config_hash: str, 
                   sequences: List[str], num_runs: int, 
                   prompts_per_sequence: Dict[str, int]) -> bool:
        """Check if all evaluations are complete for a model."""
        file_path = self.get_result_file_path(model_name, config_hash)
        if not file_path.exists():
            return False
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        for sequence in sequences:
            if sequence not in data["sequences"]:
                return False
            for run in range(1, num_runs + 1):
                run_key = f"run_{run}"
                if run_key not in data["sequences"][sequence]:
                    return False
                responses = data["sequences"][sequence][run_key]
                expected_count = prompts_per_sequence.get(sequence, 0)
                if len(responses) < expected_count:
                    return False
                for response in responses:
                    if response is None:
                        return False
                        
        return True        
    def get_next_task(self, model_name: str, config_hash: str,
                     sequences: List[str], num_runs: int,
                     prompts_per_sequence: Dict[str, int]) -> Optional[Tuple[str, int, int]]:
        """Get the next task to execute for a model."""
        file_path = self.get_result_file_path(model_name, config_hash)
        
        if not file_path.exists():
            return sequences[0], 1, 0  # First sequence, first run, first prompt
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        for sequence in sequences:
            for run in range(1, num_runs + 1):
                for prompt_idx in range(prompts_per_sequence.get(sequence, 0)):
                    if not self._task_completed(data, sequence, run, prompt_idx):
                        return sequence, run, prompt_idx
                        
        return None  # All tasks complete
        
    def _create_empty_result_structure(self, model_name: str) -> Dict[str, Any]:
        """Create empty result structure."""
        return {
            "metadata": {
                "model_name": model_name,
                "config_version": 1,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "global_settings": {}
            },
            "sequences": {},
            "evaluation_scores": {},
            "status": "in_progress"
        }
        
    def _task_completed(self, data: Dict[str, Any], sequence: str, 
                      run: int, prompt_idx: int) -> bool:
        """Check if a specific task is completed."""
        run_key = f"run_{run}"
        if sequence not in data["sequences"]:
            return False
        if run_key not in data["sequences"][sequence]:
            return False
        responses = data["sequences"][sequence][run_key]
        if len(responses) <= prompt_idx:
            return False
        return responses[prompt_idx] is not None
