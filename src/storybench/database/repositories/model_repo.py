"""Model repository for managing model configuration documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import Models
from .base import BaseRepository

class ModelRepository(BaseRepository[Models]):
    """Repository for model configuration documents."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, Models)
        
    def _get_collection_name(self) -> str:
        return "models"
        
    async def find_active(self) -> Optional[Models]:
        """Find the active model configuration."""
        results = await self.find_many({"is_active": True}, limit=1)
        return results[0] if results else None
        
    async def find_by_config_hash(self, config_hash: str) -> Optional[Models]:
        """Find model configuration by hash."""
        results = await self.find_many({"config_hash": config_hash}, limit=1)
        return results[0] if results else None
        
    async def deactivate_all(self) -> int:
        """Deactivate all model configurations."""
        result = await self.collection.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        return result.modified_count
