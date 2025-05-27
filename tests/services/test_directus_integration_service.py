"""Tests for Directus integration service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.storybench.database.services.directus_integration_service import DirectusIntegrationService
from src.storybench.clients.directus_models import StorybenchPromptsStructure, StorybenchPromptConfig
from src.storybench.database.models import Prompts


class TestDirectusIntegrationService:
    """Test suite for DirectusIntegrationService."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database."""
        return AsyncMock()
    
    @pytest.fixture  
    def mock_directus_client(self):
        """Create mock DirectusClient."""
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_database, mock_directus_client):
        """Create DirectusIntegrationService with mocks."""
        service = DirectusIntegrationService(mock_database, mock_directus_client)
        service.prompt_repo = AsyncMock()
        service.config_service = MagicMock()
        return service
    
    @pytest.fixture
    def sample_directus_data(self):
        """Create sample Directus data."""
        return StorybenchPromptsStructure(
            sequences={
                "story_sequence": [
                    StorybenchPromptConfig(name="intro", text="Write an introduction"),
                    StorybenchPromptConfig(name="body", text="Write the main story")
                ],
                "analysis_sequence": [
                    StorybenchPromptConfig(name="analyze", text="Analyze the content")
                ]
            },
            version=1,
            directus_id=123,
            created_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_sync_prompts_from_directus_success(self, service, sample_directus_data):
        """Test successful sync from Directus."""
        # Setup mocks
        service.directus_client.fetch_prompts = AsyncMock(return_value=sample_directus_data)
        service.config_service.generate_config_hash.return_value = "test_hash"
        service.prompt_repo.find_by_config_hash = AsyncMock(return_value=None)
        service.prompt_repo.deactivate_all = AsyncMock()
        service.prompt_repo.create = AsyncMock()
        
        result = await service.sync_prompts_from_directus()
        
        assert result is not None
        assert result.version == 1
        assert "story_sequence" in result.sequences
        assert "analysis_sequence" in result.sequences
        
        # Verify repo methods were called
        service.prompt_repo.deactivate_all.assert_called_once()
        service.prompt_repo.create.assert_called_once()
