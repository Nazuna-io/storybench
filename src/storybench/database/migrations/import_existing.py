"""Data migration utilities for importing existing evaluation results."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging

from ..models import Evaluation, Response, EvaluationStatus, ResponseStatus, GlobalSettings
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
                await self._import_json_file(json_file)
                stats["files_processed"] += 1
                logger.info(f"Successfully imported {json_file.name}")
                
            except Exception as e:
                logger.error(f"Error importing {json_file.name}: {e}")
                stats["errors"] += 1
                
        # Update final counts
        stats["evaluations_imported"] = await self.evaluation_repo.collection.count_documents({})
        stats["responses_imported"] = await self.response_repo.collection.count_documents({})
        
        return stats
        
    async def _import_json_file(self, json_file: Path):
        """Import a single JSON file (placeholder implementation)."""
        # This will be implemented in Phase 4
        # For now, just validate the file can be read
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        logger.info(f"JSON file {json_file.name} contains {len(data)} records")
        # Actual import logic will be added in Phase 4
