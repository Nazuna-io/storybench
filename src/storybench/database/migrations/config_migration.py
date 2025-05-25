"""Configuration migration service for moving file-based configs to MongoDB."""

import yaml
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Models, Prompts, EvaluationCriteria, ModelConfig, PromptConfig, EvaluationCriterion, EvaluationConfig
from ..services.config_service import ConfigService

logger = logging.getLogger(__name__)

class ConfigMigrationService:
    """Service for migrating file-based configurations to MongoDB."""
    
    def __init__(self, database: AsyncIOMotorDatabase, config_dir: str = "config"):
        """Initialize migration service."""
        self.database = database
        self.config_dir = Path(config_dir)
        self.config_service = ConfigService(database)
        
    async def migrate_all_configs(self) -> Dict[str, Any]:
        """Migrate all configuration files to MongoDB."""
        stats = {
            "models": {"migrated": False, "error": None},
            "prompts": {"migrated": False, "error": None},
            "evaluation_criteria": {"migrated": False, "error": None}
        }
        
        # Migrate models configuration
        try:
            models_config = await self.migrate_models_config()
            if models_config:
                stats["models"]["migrated"] = True
                stats["models"]["config_hash"] = models_config.config_hash
                logger.info(f"Successfully migrated models config with hash: {models_config.config_hash}")
        except Exception as e:
            stats["models"]["error"] = str(e)
            logger.error(f"Failed to migrate models config: {e}")
            
        # Migrate prompts configuration
        try:
            prompts_config = await self.migrate_prompts_config()
            if prompts_config:
                stats["prompts"]["migrated"] = True
                stats["prompts"]["config_hash"] = prompts_config.config_hash
                logger.info(f"Successfully migrated prompts config with hash: {prompts_config.config_hash}")
        except Exception as e:
            stats["prompts"]["error"] = str(e)
            logger.error(f"Failed to migrate prompts config: {e}")
            
        # Migrate evaluation criteria configuration
        try:
            criteria_config = await self.migrate_evaluation_criteria_config()
            if criteria_config:
                stats["evaluation_criteria"]["migrated"] = True
                stats["evaluation_criteria"]["config_hash"] = criteria_config.config_hash
                logger.info(f"Successfully migrated criteria config with hash: {criteria_config.config_hash}")
        except Exception as e:
            stats["evaluation_criteria"]["error"] = str(e)
            logger.error(f"Failed to migrate evaluation criteria config: {e}")
            
        return stats
        
    async def migrate_models_config(self) -> Optional[Models]:
        """Migrate models.yaml to MongoDB."""
        models_file = self.config_dir / "models.yaml"
        
        if not models_file.exists():
            logger.warning(f"Models config file not found: {models_file}")
            return None
            
        with open(models_file, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Convert to our Models structure
        model_configs = []
        for model_data in config_data.get("models", []):
            model_config = ModelConfig(
                name=model_data["name"],
                type=model_data["type"],
                provider=model_data["provider"],
                model_name=model_data["model_name"],
                repo_id=model_data.get("repo_id"),
                filename=model_data.get("filename"),
                subdirectory=model_data.get("subdirectory")
            )
            model_configs.append(model_config)
            
        evaluation_config = EvaluationConfig(
            auto_evaluate=config_data.get("evaluation", {}).get("auto_evaluate", False),
            evaluator_models=config_data.get("evaluation", {}).get("evaluator_models", []),
            max_retries=config_data.get("evaluation", {}).get("max_retries", 3)
        )
        
        # Save to database using ConfigService
        models_data = {
            "models": [model.dict() for model in model_configs],
            "evaluation": evaluation_config.dict()
        }
        
        return await self.config_service.save_models_config(models_data)
        
    async def migrate_prompts_config(self) -> Optional[Prompts]:
        """Migrate prompts.json to MongoDB."""
        prompts_file = self.config_dir / "prompts.json"
        
        if not prompts_file.exists():
            logger.warning(f"Prompts config file not found: {prompts_file}")
            return None
            
        with open(prompts_file, 'r') as f:
            config_data = json.load(f)
            
        # Convert to our Prompts structure
        sequences = {}
        for sequence_name, prompts_list in config_data.items():
            prompt_configs = []
            for prompt_data in prompts_list:
                prompt_config = PromptConfig(
                    name=prompt_data["name"],
                    text=prompt_data["text"]
                )
                prompt_configs.append(prompt_config)
            sequences[sequence_name] = [prompt.dict() for prompt in prompt_configs]
            
        # Save to database using ConfigService
        prompts_data = {"sequences": sequences}
        return await self.config_service.save_prompts_config(prompts_data)
        
    async def migrate_evaluation_criteria_config(self) -> Optional[EvaluationCriteria]:
        """Migrate evaluation_criteria.yaml to MongoDB."""
        criteria_file = self.config_dir / "evaluation_criteria.yaml"
        
        if not criteria_file.exists():
            logger.warning(f"Evaluation criteria config file not found: {criteria_file}")
            return None
            
        with open(criteria_file, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Convert to our EvaluationCriteria structure
        criteria = {}
        for criterion_name, criterion_data in config_data.get("criteria", {}).items():
            criterion = EvaluationCriterion(
                name=criterion_data["name"],
                description=criterion_data["description"],
                scale=criterion_data["scale"]
            )
            criteria[criterion_name] = criterion.dict()
            
        # Save to database using ConfigService
        criteria_data = {"criteria": criteria}
        return await self.config_service.save_criteria_config(criteria_data)
