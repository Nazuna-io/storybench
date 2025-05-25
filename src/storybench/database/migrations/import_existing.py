"""Data migration utilities for importing existing evaluation results."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging

from ..models import Evaluation, Response, EvaluationStatus, ResponseStatus, GlobalSettings, PyObjectId
from ..repositories import EvaluationRepository, ResponseRepository
from ..services import ConfigService

logger = logging.getLogger(__name__)

class ExistingDataImporter:
    """Imports existing JSON evaluation results into MongoDB."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.evaluation_repo = EvaluationRepository(database)
        self.response_repo = ResponseRepository(database)
        self.config_service = ConfigService(database)
    
    async def validate_import_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of imported data."""
        validation_results = {
            "total_evaluations": 0,
            "total_responses": 0,
            "orphaned_responses": 0,
            "missing_required_fields": [],
            "timestamp_anomalies": [],
            "is_valid": True
        }
        
        # Count total records
        validation_results["total_evaluations"] = await self.evaluation_repo.collection.count_documents({})
        validation_results["total_responses"] = await self.response_repo.collection.count_documents({})
        
        # Check for orphaned responses (responses without matching evaluation)
        async for response in self.response_repo.collection.find():
            evaluation_exists = await self.evaluation_repo.collection.count_documents(
                {"_id": response["evaluation_id"]}
            )
            if not evaluation_exists:
                validation_results["orphaned_responses"] += 1
                validation_results["is_valid"] = False
        
        # Check for required fields
        async for evaluation in self.evaluation_repo.collection.find():
            required_fields = ["config_hash", "timestamp", "status", "models"]
            for field in required_fields:
                if field not in evaluation or evaluation[field] is None:
                    validation_results["missing_required_fields"].append(
                        f"Evaluation {evaluation['_id']}: missing {field}"
                    )
                    validation_results["is_valid"] = False
            
            # Check timestamp consistency
            if evaluation.get("completed_at") and evaluation.get("started_at"):
                if evaluation["completed_at"] < evaluation["started_at"]:
                    validation_results["timestamp_anomalies"].append(
                        f"Evaluation {evaluation['_id']}: completed_at before started_at"
                    )
                    validation_results["is_valid"] = False
        
        # Check response completeness for each evaluation
        async for evaluation in self.evaluation_repo.collection.find():
            total_responses = await self.response_repo.collection.count_documents(
                {"evaluation_id": evaluation["_id"]}
            )
            if total_responses != evaluation.get("total_tasks", 0):
                validation_results["missing_required_fields"].append(
                    f"Evaluation {evaluation['_id']}: {total_responses} responses vs {evaluation.get('total_tasks', 0)} expected tasks"
                )
                validation_results["is_valid"] = False
        
        return validation_results
        
    async def import_from_output_directory(self, output_dir: str) -> Dict[str, int]:
        """Import all JSON files from the output directory."""
        stats = {
            "evaluations_imported": 0,
            "responses_imported": 0,
            "files_processed": 0,
            "errors": 0
        }
        
        output_path = Path(output_dir)
        if not output_path.exists():
            logger.error(f"Output directory does not exist: {output_dir}")
            return stats
            
        json_files = list(output_path.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files to import")
        
        for json_file in json_files:
            try:
                evaluation_id, responses_count = await self._import_json_file(json_file)
                stats["files_processed"] += 1
                stats["evaluations_imported"] += 1
                stats["responses_imported"] += responses_count
                logger.info(f"Successfully imported {json_file.name}: {responses_count} responses")
                
            except Exception as e:
                logger.error(f"Error importing {json_file.name}: {e}")
                stats["errors"] += 1
                
        # Remove redundant counts since we're tracking them during import
        return stats
        
    async def _import_json_file(self, json_file: Path):
        """Import a single JSON file with complete evaluation data."""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Processing {json_file.name} with metadata: {data.get('metadata', {})}")
        
        # Extract metadata
        metadata = data.get('metadata', {})
        model_name = metadata.get('model_name')
        config_version = metadata.get('config_version', 1)
        timestamp = self._parse_timestamp(metadata.get('timestamp'))
        last_updated = self._parse_timestamp(metadata.get('last_updated'))
        global_settings = metadata.get('global_settings', {})
        
        if not model_name:
            raise ValueError(f"No model_name found in {json_file.name}")
            
        # Generate config hash from filename (appears to follow pattern: model_hash.json)
        config_hash = json_file.stem.split('_')[-1] if '_' in json_file.stem else "unknown"
        
        # Count total tasks from sequences
        sequences = data.get('sequences', {})
        total_tasks = self._count_total_tasks(sequences)
        
        # Create evaluation record
        evaluation = Evaluation(
            config_hash=config_hash,
            timestamp=timestamp or datetime.utcnow(),
            status=EvaluationStatus.COMPLETED,
            models=[model_name],
            global_settings=GlobalSettings(**global_settings) if global_settings else GlobalSettings(),
            total_tasks=total_tasks,
            completed_tasks=total_tasks,  # All tasks are completed in imported data
            current_model=model_name,
            current_sequence="",
            current_run=0,
            started_at=timestamp or datetime.utcnow(),
            completed_at=last_updated or timestamp or datetime.utcnow()
        )
        
        # Insert evaluation and get ID
        evaluation_id = await self.evaluation_repo.create(evaluation)
        logger.info(f"Created evaluation {evaluation_id} for model {model_name}")
        
        # Import all responses
        responses_imported = 0
        for sequence_name, runs in sequences.items():
            for run_key, prompts in runs.items():
                run_number = int(run_key.split('_')[1]) if '_' in run_key else 1
                
                for prompt_index, prompt_data in enumerate(prompts):
                    # Debug: print the evaluation_id type and value
                    logger.info(f"Creating response with evaluation_id: {evaluation_id} (type: {type(evaluation_id)})")
                    eval_id_str = str(evaluation_id)
                    logger.info(f"Converted to string: {eval_id_str} (type: {type(eval_id_str)})")
                    
                    response = Response(
                        evaluation_id=eval_id_str,
                        model_name=model_name,
                        sequence=sequence_name,
                        run=run_number,
                        prompt_index=prompt_index,
                        prompt_name=prompt_data.get('prompt_name', ''),
                        prompt_text=prompt_data.get('prompt_text', ''),
                        response=prompt_data.get('response', ''),
                        generation_time=prompt_data.get('generation_time', 0.0),
                        completed_at=self._parse_timestamp(prompt_data.get('completed_at')) or datetime.utcnow(),
                        status=ResponseStatus.COMPLETED
                    )
                    
                    await self.response_repo.create(response)
                    responses_imported += 1
                    
        logger.info(f"Imported {responses_imported} responses for evaluation {evaluation_id}")
        return evaluation_id, responses_imported
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse ISO timestamp string into datetime object."""
        if not timestamp_str:
            return None
            
        try:
            # Remove 'Z' suffix and parse ISO format
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}")
            return None
    
    def _count_total_tasks(self, sequences: Dict[str, Any]) -> int:
        """Count total number of prompt tasks across all sequences and runs."""
        total = 0
        for sequence_name, runs in sequences.items():
            for run_key, prompts in runs.items():
                total += len(prompts)
        return total
    
    async def cleanup_file_dependencies(self, output_dir: str, create_backup: bool = True) -> Dict[str, Any]:
        """Clean up file-based dependencies after successful import."""
        cleanup_results = {
            "backup_created": False,
            "backup_path": "",
            "files_moved": 0,
            "cleanup_successful": False
        }
        
        output_path = Path(output_dir)
        
        if create_backup:
            # Create backup directory with timestamp
            backup_dir = output_path.parent / f"output_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(exist_ok=True)
            
            # Move JSON files to backup
            json_files = list(output_path.glob("*.json"))
            for json_file in json_files:
                if json_file.name != "README.md":  # Keep README
                    backup_file = backup_dir / json_file.name
                    json_file.rename(backup_file)
                    cleanup_results["files_moved"] += 1
            
            cleanup_results["backup_created"] = True
            cleanup_results["backup_path"] = str(backup_dir)
            cleanup_results["cleanup_successful"] = True
            
            logger.info(f"Moved {cleanup_results['files_moved']} files to backup: {backup_dir}")
        
        return cleanup_results
    
    async def export_for_analysis(self, output_path: str, evaluation_ids: Optional[List] = None) -> str:
        """Export evaluation data back to JSON format for external analysis."""
        export_path = Path(output_path)
        export_path.mkdir(exist_ok=True)
        
        query = {}
        if evaluation_ids:
            query["_id"] = {"$in": evaluation_ids}
        
        exported_files = []
        async for evaluation in self.evaluation_repo.collection.find(query):
            # Reconstruct original JSON format
            export_data = {
                "metadata": {
                    "model_name": evaluation["models"][0] if evaluation["models"] else "unknown",
                    "config_version": 1,
                    "timestamp": evaluation["timestamp"].isoformat() + "Z",
                    "last_updated": evaluation["completed_at"].isoformat() + "Z" if evaluation.get("completed_at") else "",
                    "global_settings": evaluation.get("global_settings", {})
                },
                "sequences": {}
            }
            
            # Get all responses for this evaluation
            responses = []
            async for response in self.response_repo.collection.find({"evaluation_id": evaluation["_id"]}):
                responses.append(response)
            
            # Group responses by sequence and run
            for response in responses:
                sequence = response["sequence"]
                run_key = f"run_{response['run']}"
                
                if sequence not in export_data["sequences"]:
                    export_data["sequences"][sequence] = {}
                if run_key not in export_data["sequences"][sequence]:
                    export_data["sequences"][sequence][run_key] = []
                
                export_data["sequences"][sequence][run_key].append({
                    "prompt_name": response["prompt_name"],
                    "prompt_text": response["prompt_text"],
                    "response": response["response"],
                    "generation_time": response["generation_time"],
                    "completed_at": response["completed_at"].isoformat() + "Z"
                })
            
            # Write export file
            model_name = evaluation["models"][0] if evaluation["models"] else "unknown"
            filename = f"{model_name}_{evaluation['config_hash']}.json"
            export_file = export_path / filename
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            exported_files.append(filename)
        
        logger.info(f"Exported {len(exported_files)} files to {export_path}")
        return str(export_path)
