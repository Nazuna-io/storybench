"""Prompt repository for managing prompt configuration documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Prompts
from .base import BaseRepository

class PromptRepository(BaseRepository[Prompts]):
    """Repository for prompt configuration documents."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, Prompts)
        
    def _get_collection_name(self) -> str:
        return "prompts"
        
    async def find_active(self) -> Optional[Prompts]:
        """Find the active prompt configuration."""
        results = await self.find_many({"is_active": True}, limit=1)
        return results[0] if results else None
        
    async def find_by_config_hash(self, config_hash: str) -> Optional[Prompts]:
        """Find prompt configuration by hash."""
        results = await self.find_many({"config_hash": config_hash}, limit=1)
        return results[0] if results else None
        
    async def deactivate_all(self) -> int:
        """Deactivate all prompt configurations."""
        result = await self.collection.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        return result.modified_count
