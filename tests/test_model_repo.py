"""
Comprehensive tests for database/repositories/model_repo.py
These tests cover the ModelRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from bson import ObjectId

# Import the repository we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.database.repositories.model_repo import ModelRepository
from storybench.database.models import Models


class TestModelRepository:
    """Test the ModelRepository class."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        database = Mock()
        database.__getitem__ = Mock(return_value=AsyncMock())
        return database
    
    @pytest.fixture
    def repository(self, mock_database):
        """Create a model repository instance."""
        return ModelRepository(mock_database)
    
    def test_model_repository_initialization(self, mock_database):
        """Test model repository initialization."""
        repo = ModelRepository(mock_database)
        
        assert repo.model_class == Models
        assert repo.collection_name == "models"
    
    @pytest.mark.asyncio
    async def test_find_active_models_found(self, repository):
        """Test finding active models when one exists."""
        # Setup mock response
        mock_models = Models(
            config_hash="abc123",
            version=1,
            models=[
                {
                    "name": "gpt-4",
                    "type": "api",
                    "provider": "openai",
                    "model_name": "gpt-4"
                }
            ],
            is_active=True
        )
        
        # Mock the find_many method
        repository.find_many = AsyncMock(return_value=[mock_models])
        
        # Execute
        result = await repository.find_active()
        
        # Verify
        assert result is not None
        assert result.config_hash == "abc123"
        assert result.is_active == True
        repository.find_many.assert_called_once_with({"is_active": True}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_active_models_not_found(self, repository):
        """Test finding active models when none exist."""
        repository.find_many = AsyncMock(return_value=[])
        
        result = await repository.find_active()
        
        assert result is None
        repository.find_many.assert_called_once_with({"is_active": True}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_by_config_hash_found(self, repository):
        """Test finding models by config hash when found."""
        config_hash = "test_hash_123"
        mock_models = Models(
            config_hash=config_hash,
            version=1,
            models=[
                {
                    "name": "test-model",
                    "type": "local",
                    "provider": "huggingface",
                    "model_name": "test-model-7b"
                }
            ],
            is_active=False
        )
        repository.find_many = AsyncMock(return_value=[mock_models])
        
        result = await repository.find_by_config_hash(config_hash)
        
        assert result is not None
        assert result.config_hash == config_hash
        repository.find_many.assert_called_once_with({"config_hash": config_hash}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_by_config_hash_not_found(self, repository):
        """Test finding models by config hash when not found."""
        config_hash = "nonexistent_hash"
        repository.find_many = AsyncMock(return_value=[])
        
        result = await repository.find_by_config_hash(config_hash)
        
        assert result is None
        repository.find_many.assert_called_once_with({"config_hash": config_hash}, limit=1)
    
    @pytest.mark.asyncio
    async def test_deactivate_all_models(self, repository):
        """Test deactivating all model configurations."""
        mock_result = Mock()
        mock_result.modified_count = 2
        repository.collection.update_many = AsyncMock(return_value=mock_result)
        
        modified_count = await repository.deactivate_all()
        
        assert modified_count == 2
        repository.collection.update_many.assert_called_once_with(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
