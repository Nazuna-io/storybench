"""Criteria repository for managing evaluation criteria documents."""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models import EvaluationCriteria
from .base import BaseRepository

class CriteriaRepository(BaseRepository[EvaluationCriteria]):
    """Repository for evaluation criteria documents."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, EvaluationCriteria)
        
    def _get_collection_name(self) -> str:
        return "evaluation_criteria"
        
    async def find_active(self) -> Optional[EvaluationCriteria]:
        """Find the active evaluation criteria configuration."""
        results = await self.find_many({"is_active": True}, limit=1)
        return results[0] if results else None
        
    async def find_by_config_hash(self, config_hash: str) -> Optional[EvaluationCriteria]:
        """Find evaluation criteria by hash."""
        results = await self.find_many({"config_hash": config_hash}, limit=1)
        return results[0] if results else None
        
    async def deactivate_all(self) -> int:
        """Deactivate all evaluation criteria configurations."""
        result = await self.collection.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        return result.modified_count
