"""Service for managing evaluation results."""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ...models.progress import ProgressTracker
from ..models.responses import ResultSummary, DetailedResult, EvaluationScores, ResultMetadata


class ResultsService:
    """Service for managing evaluation results."""
    
    def __init__(self, results_dir: str = "output"):
        """Initialize results service."""
        self.results_dir = Path(results_dir)
        self.tracker = ProgressTracker(results_dir)
        
    async def get_all_results(self, config_version: Optional[str] = None) -> List[ResultSummary]:
        """Get all results with optional filtering."""
        results = []
        
        if not self.results_dir.exists():
            return results
            
        # Find all result files
        for result_file in self.results_dir.glob("*.json"):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    
                # Filter by config version if specified
                if config_version and config_hash != config_version:
                    continue
                    
                summary = self._create_result_summary(data, result_file.name)
                if summary:
                    results.append(summary)
                    
            except Exception as e:
                # Skip corrupted files
                continue
                
        # Sort by timestamp, most recent first
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results        
    async def get_detailed_result(self, model_name: str, config_version: Optional[str] = None) -> Optional[DetailedResult]:
        """Get detailed results for a specific model."""
        # Find matching result file
        safe_name = model_name.replace("/", "_").replace(" ", "_")
        
        if config_version:
            result_file = self.results_dir / f"{safe_name}_{config_version}.json"
        else:
            # Find the most recent result file for this model
            matching_files = list(self.results_dir.glob(f"{safe_name}_*.json"))
            if not matching_files:
                return None
            result_file = max(matching_files, key=lambda f: f.stat().st_mtime)
            
        if not result_file.exists():
            return None
            
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                
            return self._create_detailed_result(data)
            
        except Exception:
            return None
            
    async def get_available_versions(self) -> List[str]:
        """Get list of available configuration versions."""
        versions = set()
        
        if not self.results_dir.exists():
            return []
            
        for result_file in self.results_dir.glob("*.json"):
            try:
                # Extract config hash from filename (format: ModelName_confighash.json)
                filename = result_file.name
                if '_' in filename:
                    config_hash = filename.split('_')[-1].replace('.json', '')
                    versions.add(config_hash)
            except Exception:
                continue
                
        return sorted(list(versions))        
    def _create_result_summary(self, data: Dict[str, Any], filename: str) -> Optional[ResultSummary]:
        """Create a result summary from result data."""
        try:
            metadata = data.get("metadata", {})
            model_name = metadata.get("model_name", "Unknown")
            config_hash = filename.split('_')[-1].replace('.json', '')  # Extract from filename
            timestamp_str = metadata.get("timestamp", datetime.now().isoformat())
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Calculate completion status
            sequences = data.get("sequences", {})
            total_responses = 0
            successful_responses = 0
            
            for sequence_data in sequences.values():
                for run_data in sequence_data.values():
                    if isinstance(run_data, list):  # New format: run_data is a list
                        for response in run_data:
                            total_responses += 1
                            if response.get("response") and not response.get("error"):
                                successful_responses += 1
                    else:  # Old format: run_data is a dict
                        for response in run_data.values():
                            total_responses += 1
                            if response.get("response") and not response.get("error"):
                                successful_responses += 1
            
            # Determine status
            status = data.get("status", "unknown")
            if status == "unknown":
                if successful_responses == total_responses and total_responses > 0:
                    status = "completed"
                elif successful_responses > 0:
                    status = "in_progress"
                else:
                    status = "failed"
                
            # Get evaluation scores
            eval_scores = data.get("evaluation_scores", {})
            scores = EvaluationScores(
                overall=eval_scores.get("overall"),
                creativity=eval_scores.get("creativity"),
                coherence=eval_scores.get("coherence"),
                originality=eval_scores.get("originality"),
                engagement=eval_scores.get("engagement")
            )
            
            return ResultSummary(
                model_name=model_name,
                config_version=config_hash,
                status=status,
                timestamp=timestamp,
                scores=scores,
                total_responses=total_responses,
                successful_responses=successful_responses
            )
            
        except Exception as e:
            print(f"Error creating result summary: {e}")  # Debug
            return None        
    def _create_detailed_result(self, data: Dict[str, Any]) -> DetailedResult:
        """Create detailed result from result data."""
        model_name = data.get("model_name", "Unknown")
        config_hash = data.get("config_hash", "unknown")
        timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        
        # Create metadata
        metadata = ResultMetadata(
            model_name=model_name,
            config_version=config_hash,
            config_details=data.get("config_details", {}),
            timestamp=timestamp,
            last_updated=datetime.fromisoformat(data.get("last_updated", timestamp.isoformat()))
        )
        
        # Extract sequences data
        sequences = data.get("sequences", {})
        
        # Calculate status
        total_responses = 0
        successful_responses = 0
        
        for sequence_data in sequences.values():
            for run_data in sequence_data.values():
                for response in run_data.values():
                    total_responses += 1
                    if response.get("response") and not response.get("error"):
                        successful_responses += 1
        
        if successful_responses == total_responses and total_responses > 0:
            status = "completed"
        elif successful_responses > 0:
            status = "in_progress"
        else:
            status = "failed"
            
        # Placeholder scores (would integrate with actual evaluation logic)
        scores = EvaluationScores(
            overall=None,
            creativity=None,
            coherence=None,
            originality=None,
            engagement=None
        )
        
        return DetailedResult(
            metadata=metadata,
            sequences=sequences,
            evaluation_scores=scores,
            status=status
        )