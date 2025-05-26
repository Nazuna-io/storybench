"""Configuration service for managing versioned configurations."""

import hashlib
import json
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Models, Prompts, EvaluationCriteria
from ..repositories import ModelRepository, PromptRepository, CriteriaRepository

class ConfigService:
    """Service for managing configuration versions and hashes."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.model_repo = ModelRepository(database)
        self.prompt_repo = PromptRepository(database)
        self.criteria_repo = CriteriaRepository(database)
        
    def generate_config_hash(self, config_data: Dict[str, Any]) -> str:
        """Generate a hash for configuration data."""
        # Sort keys for consistent hashing
        config_str = json.dumps(config_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
        
    async def get_active_models(self) -> Optional[Models]:
        """Get the currently active models configuration."""
        return await self.model_repo.find_active()
        
    async def get_active_prompts(self) -> Optional[Prompts]:
        """Get the currently active prompts configuration."""
        return await self.prompt_repo.find_active()
        
    async def get_active_criteria(self) -> Optional[EvaluationCriteria]:
        """Get the currently active evaluation criteria."""
        return await self.criteria_repo.find_active()
        
    async def save_models_config(self, models_data: Dict[str, Any]) -> Models:
        """Save a new models configuration."""
        config_hash = self.generate_config_hash(models_data)
        
        # Check if this configuration already exists
        existing = await self.model_repo.find_by_config_hash(config_hash)
        if existing:
            if not existing.is_active:
                # Deactivate all other configurations first
                await self.model_repo.deactivate_all()
                # Activate the existing one that matches the hash
                await self.model_repo.update_by_id(existing.id, {"is_active": True})
                existing.is_active = True  # Update the in-memory object
            return existing
            
        # Deactivate current active configuration
        await self.model_repo.deactivate_all()
        
        # Create new configuration
        models_config = Models(
            config_hash=config_hash,
            **models_data
        )
        
        return await self.model_repo.create(models_config)
        
    async def save_prompts_config(self, prompts_data: Dict[str, Any]) -> Prompts:
        """Save a new prompts configuration."""
        config_hash = self.generate_config_hash(prompts_data)
        
        # Check if this configuration already exists
        existing = await self.prompt_repo.find_by_config_hash(config_hash)
        if existing:
            return existing
            
        # Deactivate current active configuration
        await self.prompt_repo.deactivate_all()
        
        # Create new configuration
        prompts_config = Prompts(
            config_hash=config_hash,
            **prompts_data
        )
        
        return await self.prompt_repo.create(prompts_config)
        
    async def save_criteria_config(self, criteria_data: Dict[str, Any]) -> EvaluationCriteria:
        """Save a new evaluation criteria configuration."""
        config_hash = self.generate_config_hash(criteria_data)
        
        # Check if this configuration already exists
        existing = await self.criteria_repo.find_by_config_hash(config_hash)
        if existing:
            return existing
            
        # Deactivate current active configuration
        await self.criteria_repo.deactivate_all()
        
        # Create new configuration
        criteria_config = EvaluationCriteria(
            config_hash=config_hash,
            **criteria_data
        )
        
        return await self.criteria_repo.create(criteria_config)
