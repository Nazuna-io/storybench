"""Directus integration service for replacing MongoDB prompt data."""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from ...clients.directus_client import DirectusClient, DirectusClientError
from ...clients.directus_models import StorybenchPromptsStructure
from ..models import Prompts, PromptItemConfig
from ..repositories.prompt_repo import PromptRepository
from .config_service import ConfigService


class DirectusIntegrationService:
    """Service to integrate Directus CMS with existing storybench prompt system."""
    
    def __init__(self, database: AsyncIOMotorDatabase, directus_client: DirectusClient = None):
        """Initialize the integration service."""
        self.database = database
        self.directus_client = directus_client or DirectusClient()
        self.prompt_repo = PromptRepository(database)
        self.config_service = ConfigService(database)
    
    async def sync_prompts_from_directus(self, version_number: Optional[int] = None) -> Optional[Prompts]:
        """Sync prompts from Directus to MongoDB.
        
        Args:
            version_number: Specific version to sync. If None, syncs latest published version.
            
        Returns:
            Prompts document or None if no data found.
        """
        try:
            # Fetch from Directus
            directus_data = await self.directus_client.fetch_prompts(version_number)
            if not directus_data:
                return None
            
            # Convert to MongoDB format
            mongodb_prompts = self._convert_to_mongodb_format(directus_data)
            
            # Save to MongoDB
            await self._save_prompts_to_mongodb(mongodb_prompts)
            
            return mongodb_prompts
            
        except DirectusClientError as e:
            raise Exception(f"Failed to sync prompts from Directus: {str(e)}")
    
    def _convert_to_mongodb_format(self, directus_data: StorybenchPromptsStructure) -> Prompts:
        """Convert Directus format to MongoDB Prompts format."""
        # Convert sequences to the expected format
        mongodb_sequences = {}
        for seq_name, prompts in directus_data.sequences.items():
            mongodb_sequences[seq_name] = [
                PromptItemConfig(name=p.name, text=p.text)
                for p in prompts
            ]
        
        # Generate config hash
        config_hash = self.config_service.generate_config_hash({
            "sequences": {k: [{"name": p.name, "text": p.text} for p in v] 
                         for k, v in mongodb_sequences.items()},
            "version": directus_data.version,
            "directus_id": directus_data.directus_id
        })
        
        return Prompts(
            config_hash=config_hash,
            version=directus_data.version,
            sequences=mongodb_sequences,
            created_at=directus_data.created_at,
            is_active=True
        )
    
    async def _save_prompts_to_mongodb(self, prompts: Prompts) -> None:
        """Save prompts to MongoDB, deactivating existing ones."""
        # Check if this configuration already exists
        existing = await self.prompt_repo.find_by_config_hash(prompts.config_hash)
        
        if existing:
            # If exists but not active, activate it
            if not existing.is_active:
                await self.prompt_repo.deactivate_all()
                await self.prompt_repo.update_by_id(existing.id, {"is_active": True})
        else:
            # Deactivate all existing prompts and save new one
            await self.prompt_repo.deactivate_all()
            await self.prompt_repo.create(prompts)
    
    async def get_active_prompts(self) -> Optional[Prompts]:
        """Get currently active prompts (MongoDB format)."""
        return await self.prompt_repo.find_active()
    
    async def refresh_prompts(self) -> Optional[Prompts]:
        """Refresh prompts by fetching latest from Directus."""
        return await self.sync_prompts_from_directus()
    
    async def test_directus_connection(self) -> bool:
        """Test connection to Directus CMS."""
        return await self.directus_client.test_connection()
    
    async def list_available_versions(self) -> list:
        """List all available published versions from Directus."""
        try:
            versions = await self.directus_client.list_published_versions()
            return [
                {
                    "version_number": v.version_number,
                    "name": v.version_name,  # Updated field name
                    "description": v.description,
                    "date_created": v.date_created,
                    "date_updated": v.date_updated
                }
                for v in versions
            ]
        except DirectusClientError as e:
            raise Exception(f"Failed to list versions: {str(e)}")
