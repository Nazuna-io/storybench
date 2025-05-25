"""Configuration migration service for moving file-based configs to MongoDB."""

import yaml
import json
import os
import logging
import hashlib # Added for hashing
from typing import Dict, Any, Optional
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Models, Prompts, EvaluationCriteria, ModelConfigItem, PromptItemConfig, EvaluationCriterionItem, EvaluationRunConfig
from ..repositories import ModelRepository, PromptRepository, CriteriaRepository

logger = logging.getLogger(__name__)

class ConfigMigrationService:
    """Service for migrating file-based configurations to MongoDB."""
    
    def __init__(self, database: AsyncIOMotorDatabase, config_dir: str = "config"):
        """Initialize migration service."""
        self.database = database
        self.config_dir = Path(config_dir)
        self.models_repo = ModelRepository(database)
        self.prompts_repo = PromptsRepository(database) # Assuming PromptsRepository exists and is importable
        self.criteria_repo = CriteriaRepository(database)

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of a dictionary after canonical JSON serialization."""
        # Serialize to JSON string with sorted keys for a canonical representation
        canonical_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
        
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

        config_hash = self._calculate_data_hash(config_data)
        existing_config = await self.models_repo.find_by_config_hash(config_hash)
        if existing_config:
            logger.info(f"Models config with hash {config_hash} already exists. Skipping migration.")
            return existing_config
            
        # Convert to our Models structure
        model_configs_items = []
        for model_data in config_data.get("models", []):
            model_config_item = ModelConfigItem(
                name=model_data["name"],
                type=model_data["type"],
                provider=model_data["provider"],
                model_name=model_data["model_name"],
                repo_id=model_data.get("repo_id"),
                filename=model_data.get("filename"),
                subdirectory=model_data.get("subdirectory")
            )
            model_configs_items.append(model_config_item)
            
        evaluation_run_config_data = config_data.get("evaluation", {})
        evaluation_run_config = EvaluationRunConfig(
            auto_evaluate_generated_responses=evaluation_run_config_data.get("auto_evaluate_generated_responses", True),
            evaluator_llm_names=evaluation_run_config_data.get("evaluator_llm_names", []),
            max_retries_on_evaluation_failure=evaluation_run_config_data.get("max_retries_on_evaluation_failure", 3)
        )
        
        models_doc = Models(
            config_hash=config_hash,
            models=model_configs_items,
            evaluation=evaluation_run_config,
            is_active=True, # Will be set after deactivating others
            version=1 # Default to 1 for a new hash, can be refined later
        )

        await self.models_repo.deactivate_all()
        # It's possible a race condition if another process activates; for CLI, likely fine.
        # More robust: get max version, increment, then create.
        # For now, keeping it simple as new hash = new version 1 active config.
        
        # Find max version if any config (even inactive) exists, to correctly set version for new one
        # This logic is a bit simplified; a true version increment would be on logical changes, not just new hash.
        all_configs = await self.models_repo.find_many({})
        if all_configs:
            max_version = max(c.version for c in all_configs if hasattr(c, 'version'))
            models_doc.version = max_version + 1
        else:
            models_doc.version = 1

        created_doc = await self.models_repo.create(models_doc)
        logger.info(f"Successfully migrated models config. New active version: {created_doc.version}, hash: {created_doc.config_hash}")
        return created_doc
        
    async def migrate_prompts_config(self) -> Optional[Prompts]:
        """Migrate prompts.json to MongoDB."""
        prompts_file = self.config_dir / "prompts.json"
        
        if not prompts_file.exists():
            logger.warning(f"Prompts config file not found: {prompts_file}")
            return None
            
        with open(prompts_file, 'r') as f:
            config_data = json.load(f)

        config_hash = self._calculate_data_hash(config_data)
        existing_config = await self.prompts_repo.find_by_config_hash(config_hash)
        if existing_config:
            logger.info(f"Prompts config with hash {config_hash} already exists. Skipping migration.")
            return existing_config
            
        # Convert to our Prompts structure
        sequences_items: Dict[str, List[PromptItemConfig]] = {}
        for sequence_name, prompts_list_data in config_data.items(): # Assuming config_data is the top-level dict of sequences
            prompt_item_configs = []
            for prompt_data in prompts_list_data:
                prompt_item_config = PromptItemConfig(
                    name=prompt_data["name"],
                    text=prompt_data["text"]
                )
                prompt_item_configs.append(prompt_item_config)
            sequences_items[sequence_name] = prompt_item_configs
            
        prompts_doc = Prompts(
            config_hash=config_hash,
            sequences=sequences_items,
            is_active=True, # Will be set after deactivating others
            version=1 # Default to 1 for new hash
        )

        await self.prompts_repo.deactivate_all()
        
        all_configs = await self.prompts_repo.find_many({})
        if all_configs:
            max_version = max(c.version for c in all_configs if hasattr(c, 'version'))
            prompts_doc.version = max_version + 1
        else:
            prompts_doc.version = 1

        created_doc = await self.prompts_repo.create(prompts_doc)
        logger.info(f"Successfully migrated prompts config. New active version: {created_doc.version}, hash: {created_doc.config_hash}")
        return created_doc
        
    async def migrate_evaluation_criteria_config(self) -> Optional[EvaluationCriteria]:
        """Migrate evaluation_criteria.yaml to MongoDB."""
        criteria_file = self.config_dir / "evaluation_criteria.yaml"
        
        if not criteria_file.exists():
            logger.warning(f"Evaluation criteria config file not found: {criteria_file}")
            return None
            
        with open(criteria_file, 'r') as f:
            config_data = yaml.safe_load(f) # This is the full dict from YAML

        config_hash = self._calculate_data_hash(config_data) # Hash the entire YAML content
        existing_config = await self.criteria_repo.find_by_config_hash(config_hash)
        if existing_config:
            logger.info(f"Evaluation criteria config with hash {config_hash} already exists. Skipping migration.")
            return existing_config
            
        # Convert to our EvaluationCriteria structure
        criteria_items: Dict[str, EvaluationCriterionItem] = {}
        # The actual criteria are usually under a top-level key, e.g., "criteria"
        for criterion_name, criterion_data in config_data.get("criteria", {}).items():
            criterion_item = EvaluationCriterionItem(
                name=criterion_data["name"],
                description=criterion_data["description"],
                scale=criterion_data["scale"]
            )
            criteria_items[criterion_name] = criterion_item
            
        criteria_doc = EvaluationCriteria(
            config_hash=config_hash,
            criteria=criteria_items,
            is_active=True, # Will be set after deactivating others
            version=1 # Default to 1 for new hash
        )

        await self.criteria_repo.deactivate_all()
        
        all_configs = await self.criteria_repo.find_many({})
        if all_configs:
            max_version = max(c.version for c in all_configs if hasattr(c, 'version'))
            criteria_doc.version = max_version + 1
        else:
            criteria_doc.version = 1

        created_doc = await self.criteria_repo.create(criteria_doc)
        logger.info(f"Successfully migrated evaluation_criteria config. New active version: {created_doc.version}, hash: {created_doc.config_hash}")
        return created_doc
