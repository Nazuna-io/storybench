"""
Comprehensive tests for database/repositories/criteria_repo.py
These tests cover the CriteriaRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from bson import ObjectId

# Import the repository we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.database.repositories.criteria_repo import CriteriaRepository
from storybench.database.models import EvaluationCriteria


class TestCriteriaRepository:
    """Test the CriteriaRepository class."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        database = Mock()
        database.__getitem__ = Mock(return_value=AsyncMock())
        return database
    
    @pytest.fixture
    def repository(self, mock_database):
        """Create a criteria repository instance."""
        return CriteriaRepository(mock_database)
    
    def test_criteria_repository_initialization(self, mock_database):
        """Test criteria repository initialization."""
        repo = CriteriaRepository(mock_database)
        
        assert repo.model_class == EvaluationCriteria
        assert repo.collection_name == "evaluation_criteria"
    
    @pytest.mark.asyncio
    async def test_find_active_criteria_found(self, repository):
        """Test finding active criteria when one exists."""
        # Setup mock response
        mock_criteria_data = [
            {
                "_id": ObjectId(),
                "config_hash": "abc123",
                "version": 1,
                "criteria": {
                    "coherence": {
                        "name": "coherence",
                        "description": "test criterion",
                        "scale": 5
                    }
                },
                "is_active": True
            }
        ]
        
        # Mock the find_many method that would be called
        repository.find_many = AsyncMock(return_value=[
            EvaluationCriteria(**mock_criteria_data[0])
        ])
        
        # Execute
        result = await repository.find_active()
        
        # Verify
        assert result is not None
        assert result.config_hash == "abc123"
        assert result.is_active == True
        repository.find_many.assert_called_once_with({"is_active": True}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_active_criteria_not_found(self, repository):
        """Test finding active criteria when none exist."""
        # Mock empty result
        repository.find_many = AsyncMock(return_value=[])
        
        # Execute
        result = await repository.find_active()
        
        # Verify
        assert result is None
        repository.find_many.assert_called_once_with({"is_active": True}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_by_config_hash_found(self, repository):
        """Test finding criteria by config hash when found."""
        # Setup
        config_hash = "test_hash_123"
        mock_criteria = EvaluationCriteria(
            config_hash=config_hash,
            version=1,
            criteria={
                "creativity": {
                    "name": "creativity",
                    "description": "test criterion",
                    "scale": 5
                }
            },
            is_active=False
        )
        repository.find_many = AsyncMock(return_value=[mock_criteria])
        
        # Execute
        result = await repository.find_by_config_hash(config_hash)
        
        # Verify
        assert result is not None
        assert result.config_hash == config_hash
        repository.find_many.assert_called_once_with({"config_hash": config_hash}, limit=1)
    
    @pytest.mark.asyncio
    async def test_find_by_config_hash_not_found(self, repository):
        """Test finding criteria by config hash when not found."""
        # Setup
        config_hash = "nonexistent_hash"
        repository.find_many = AsyncMock(return_value=[])
        
        # Execute
        result = await repository.find_by_config_hash(config_hash)
        
        # Verify
        assert result is None
        repository.find_many.assert_called_once_with({"config_hash": config_hash}, limit=1)
    
    @pytest.mark.asyncio
    async def test_deactivate_all_criteria(self, repository):
        """Test deactivating all criteria configurations."""
        # Setup mock collection response
        mock_result = Mock()
        mock_result.modified_count = 3
        repository.collection.update_many = AsyncMock(return_value=mock_result)
        
        # Execute
        modified_count = await repository.deactivate_all()
        
        # Verify
        assert modified_count == 3
        repository.collection.update_many.assert_called_once_with(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
    
    @pytest.mark.asyncio
    async def test_deactivate_all_criteria_none_active(self, repository):
        """Test deactivating criteria when none are active."""
        # Setup mock collection response
        mock_result = Mock()
        mock_result.modified_count = 0
        repository.collection.update_many = AsyncMock(return_value=mock_result)
        
        # Execute
        modified_count = await repository.deactivate_all()
        
        # Verify
        assert modified_count == 0
        repository.collection.update_many.assert_called_once_with(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
