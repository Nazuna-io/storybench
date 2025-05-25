"""Repository for API keys management."""

from typing import Dict, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models import ApiKeys
from .base import BaseRepository
from ...utils.encryption import encryption_service


class ApiKeysRepository(BaseRepository):
    """Repository for managing encrypted API keys."""

    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database)
        self.collection = database.api_keys

    async def save_api_key(self, provider: str, api_key: str) -> bool:
        """Save an encrypted API key for a provider."""
        try:
            encrypted_key = encryption_service.encrypt(api_key)
            
            # Update existing or create new
            result = await self.collection.replace_one(
                {"provider": provider},
                {
                    "provider": provider,
                    "encrypted_key": encrypted_key,
                    "created_at": ApiKeys().created_at,
                    "updated_at": ApiKeys().updated_at,
                    "is_active": True
                },
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            print(f"Failed to save API key for {provider}: {e}")
            return False

    async def get_api_key(self, provider: str) -> Optional[str]:
        """Get decrypted API key for a provider."""
        try:
            doc = await self.collection.find_one({"provider": provider, "is_active": True})
            if doc and doc.get("encrypted_key"):
                return encryption_service.decrypt(doc["encrypted_key"])
            return None
        except Exception as e:
            print(f"Failed to get API key for {provider}: {e}")
            return None

    async def get_all_masked_keys(self) -> Dict[str, str]:
        """Get all API keys with masked values for display."""
        result = {}
        try:
            async for doc in self.collection.find({"is_active": True}):
                provider = doc["provider"]
                encrypted_key = doc.get("encrypted_key", "")
                if encrypted_key:
                    decrypted = encryption_service.decrypt(encrypted_key)
                    result[provider] = encryption_service.mask_key(decrypted)
                else:
                    result[provider] = ""
            return result
        except Exception as e:
            print(f"Failed to get masked API keys: {e}")
            return {}
    async def get_all_keys(self) -> Dict[str, str]:
        """Get all decrypted API keys. Use with caution."""
        result = {}
        try:
            async for doc in self.collection.find({"is_active": True}):
                provider = doc["provider"]
                encrypted_key = doc.get("encrypted_key", "")
                if encrypted_key:
                    result[provider] = encryption_service.decrypt(encrypted_key)
            return result
        except Exception as e:
            print(f"Failed to get API keys: {e}")
            return {}

    async def delete_api_key(self, provider: str) -> bool:
        """Delete an API key for a provider."""
        try:
            result = await self.collection.delete_one({"provider": provider})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Failed to delete API key for {provider}: {e}")
            return False

    async def get_providers(self) -> List[str]:
        """Get list of providers with API keys."""
        try:
            providers = await self.collection.distinct("provider", {"is_active": True})
            return providers
        except Exception as e:
            print(f"Failed to get providers: {e}")
            return []
