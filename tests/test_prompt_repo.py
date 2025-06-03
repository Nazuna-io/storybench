"""
Comprehensive tests for database/repositories/prompt_repo.py
These tests cover the PromptRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from bson import ObjectId

# Import the repository we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.database.repositories.prompt_repo import PromptRepository
from storybench.database.models import Prompts


class TestPromptRepository:
    """Test the PromptRepository class."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        database = Mock()
        database.__getitem__ = Mock(return_value=AsyncMock())
        return database
    
    @pytest.fixture
    def repository(self, mock_database):
        """Create a prompt repository instance."""
        return PromptRepository(mock_database)
    
    def test_prompt_repository_initialization(self, mock_database):
        """Test prompt repository initialization."""
        repo = PromptRepository(mock_database)
        
        assert repo.model_class == Prompts
        assert repo.collection_name == "prompts"
    
    @pytest.mark.asyncio
    async def test_find_active_prompts_found(self, repository):
        """Test finding active prompts when one exists."""
        mock_prompts = Prompts(
            config_hash="def456",
            version=1,
            sequences={
                "creativity_test": [
                    {
                        "name": "creativity_prompt",
                        "text": "Be creative: {topic}"
                    }
                ]
            },
            is_active=True
        )
        
        repository.find_many = AsyncMock(return_value=[mock_prompts])
        
        result = await repository.find_active()
        
        assert result is not None
        assert result.config_hash == "def456"
        assert result.is_active == True
        repository.find_many.assert_called_once_with({"is_active": True}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_active_prompts_not_found(self, repository):
        """Test finding active prompts when none exist."""
        repository.find_many = AsyncMock(return_value=[])
        
        result = await repository.find_active()
        
        assert result is None
        repository.find_many.assert_called_once_with({"is_active": True}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_by_config_hash_found(self, repository):
        """Test finding prompts by config hash when found."""
        config_hash = "prompt_hash_789"
        mock_prompts = Prompts(
            config_hash=config_hash,
            version=1,
            sequences={
                "test_sequence": [
                    {
                        "name": "test_prompt",
                        "text": "Test prompt text"
                    }
                ]
            },
            is_active=False
        )
        repository.find_many = AsyncMock(return_value=[mock_prompts])
        
        result = await repository.find_by_config_hash(config_hash)
        
        assert result is not None
        assert result.config_hash == config_hash
        repository.find_many.assert_called_once_with({"config_hash": config_hash}, limit=1)
    
    @pytest.mark.asyncio
    async def test_deactivate_all_prompts(self, repository):
        """Test deactivating all prompt configurations."""
        mock_result = Mock()
        mock_result.modified_count = 1
        repository.collection.update_many = AsyncMock(return_value=mock_result)
        
        modified_count = await repository.deactivate_all()
        
        assert modified_count == 1
        repository.collection.update_many.assert_called_once_with(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
