"""Configuration management service."""

import hashlib
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..repositories.base import Repository
from ...models.config import Config, ModelConfig, GlobalSettings, EvaluationConfig


class ConfigService:
    """Service for managing storybench configuration."""
    
    def __init__(self, repository: Repository):
        """Initialize with repository for data access."""
        self.repository = repository
    
    async def get_models_config(self) -> Dict[str, Any]:
        """Get current models configuration."""
        return await self.repository.load_models_config()
    
    async def update_models_config(self, config_data: Dict[str, Any]) -> None:
        """Update models configuration."""
        await self.repository.save_models_config(config_data)
    
    async def get_prompts(self) -> Dict[str, List[Dict[str, str]]]:
        """Get current prompts configuration."""
        return await self.repository.load_prompts()
    
    async def update_prompts(self, prompts: Dict[str, List[Dict[str, str]]]) -> None:
        """Update prompts configuration."""
        await self.repository.save_prompts(prompts)
    
    async def get_evaluation_criteria(self) -> Dict[str, Any]:
        """Get evaluation criteria configuration."""
        return await self.repository.load_evaluation_criteria()
    
    async def update_evaluation_criteria(self, criteria: Dict[str, Any]) -> None:
        """Update evaluation criteria configuration."""
        await self.repository.save_evaluation_criteria(criteria)

    async def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys (masked for security)."""
        keys = await self.repository.load_api_keys()
        # Mask the keys for display
        masked_keys = {}
        for key, value in keys.items():
            if value:
                if len(value) > 8:
                    masked_keys[key] = value[:4] + "..." + value[-4:]
                else:
                    masked_keys[key] = "***"
            else:
                masked_keys[key] = None
        return masked_keys
    
    async def update_api_keys(self, keys: Dict[str, Optional[str]]) -> None:
        """Update API keys."""
        await self.repository.save_api_keys(keys)
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration using existing Config class."""
        try:
            # Load configuration using existing Config class
            config = Config.load_config("config/models.yaml")
            errors = config.validate()
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "config_hash": config.get_version_hash()
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "config_hash": None
            }
    
    async def get_configuration_version_hash(self) -> str:
        """Get current configuration version hash."""
        try:
            config = Config.load_config("config/models.yaml")
            return config.get_version_hash()
        except Exception:
            return "unknown"
            
    async def load_config(self) -> Config:
        """Load the current configuration."""
        return Config.load_config("config/models.yaml")
