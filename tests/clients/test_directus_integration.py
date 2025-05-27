"""Integration tests for Directus client - tests against actual Directus API."""

import pytest
import asyncio
from datetime import datetime

from src.storybench.clients.directus_client import DirectusClient, DirectusClientError
from src.storybench.clients.directus_models import PublicationStatus


class TestDirectusClientIntegration:
    """Integration tests that call the actual Directus API."""
    
    @pytest.fixture
    def client(self):
        """Create DirectusClient using environment variables."""
        return DirectusClient(timeout=90)  # Longer timeout for serverless spinup
    
    @pytest.mark.asyncio
    async def test_connection(self, client):
        """Test basic connection to Directus API."""
        is_connected = await client.test_connection()
        assert is_connected is True
    
    @pytest.mark.asyncio
    async def test_fetch_latest_published_version(self, client):
        """Test fetching the latest published version."""
        version = await client.get_latest_published_version()
        
        # Should find at least version 1
        assert version is not None
        assert version.version_number >= 1
        assert version.status == PublicationStatus.PUBLISHED
        assert version.sequences_in_set is not None
        assert len(version.sequences_in_set) > 0
        
        # Check that sequences have prompts
        for sequence_junction in version.sequences_in_set:
            sequence = sequence_junction.prompt_sequences_id
            assert sequence.status == PublicationStatus.PUBLISHED
            assert sequence.prompts_in_sequence is not None
            assert len(sequence.prompts_in_sequence) > 0
            
            # Check that prompts are published
            for prompt_junction in sequence.prompts_in_sequence:
                prompt = prompt_junction.prompts_id
                assert prompt.status == PublicationStatus.PUBLISHED
                assert prompt.name
                assert prompt.text
    
    @pytest.mark.asyncio
    async def test_fetch_version_by_number(self, client):
        """Test fetching a specific version by number."""
        version = await client.get_version_by_number(1)
        
        assert version is not None
        assert version.version_number == 1
        assert version.status == PublicationStatus.PUBLISHED
    
    @pytest.mark.asyncio
    async def test_convert_to_storybench_format(self, client):
        """Test conversion to storybench format."""
        version = await client.get_latest_published_version()
        assert version is not None
        
        storybench_data = await client.convert_to_storybench_format(version)
        
        assert storybench_data.version == version.version_number
        assert storybench_data.directus_id == version.id
        assert len(storybench_data.sequences) > 0
        
        # Check that sequences contain prompts in the correct format
        for seq_name, prompts in storybench_data.sequences.items():
            assert len(prompts) > 0
            for prompt in prompts:
                assert prompt.name
                assert prompt.text
    
    @pytest.mark.asyncio
    async def test_fetch_prompts_default_version(self, client):
        """Test the main fetch_prompts method with default (latest) version."""
        prompts = await client.fetch_prompts()
        
        assert prompts is not None
        assert prompts.version >= 1
        assert len(prompts.sequences) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_prompts_specific_version(self, client):
        """Test the main fetch_prompts method with specific version."""
        prompts = await client.fetch_prompts(version_number=1)
        
        assert prompts is not None
        assert prompts.version == 1
        assert len(prompts.sequences) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_nonexistent_version(self, client):
        """Test fetching a version that doesn't exist."""
        prompts = await client.fetch_prompts(version_number=999)
        assert prompts is None
    
    @pytest.mark.asyncio
    async def test_list_published_versions(self, client):
        """Test listing all published versions."""
        versions = await client.list_published_versions()
        
        assert len(versions) > 0
        assert all(v.status == PublicationStatus.PUBLISHED for v in versions)
        assert all(v.version_number >= 1 for v in versions)
        
        # Should be sorted by version number descending
        version_numbers = [v.version_number for v in versions]
        assert version_numbers == sorted(version_numbers, reverse=True)
    
    @pytest.mark.asyncio 
    async def test_error_handling_invalid_token(self):
        """Test error handling with invalid token."""
        invalid_client = DirectusClient(token="invalid-token", timeout=30)
        
        with pytest.raises(DirectusClientError):
            await invalid_client.get_latest_published_version()
