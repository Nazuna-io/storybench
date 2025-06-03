"""
Comprehensive tests for database/repositories/base.py
These tests cover the base repository pattern with mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional

# Import the repository we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.database.repositories.base import BaseRepository
from storybench.database.models import PyObjectId


# Create a test model for testing
class TestModel(BaseModel):
    """Test Pydantic model for repository testing."""
    id: Optional[PyObjectId] = None
    name: str
    value: int


# Create a concrete implementation for testing
class TestRepository(BaseRepository[TestModel]):
    """Concrete repository implementation for testing."""
    
    def _get_collection_name(self) -> str:
        return "test_collection"


class TestBaseRepository:
    """Test the BaseRepository class."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        return Mock()
    
    @pytest.fixture
    def mock_collection(self):
        """Create a mock collection."""
        collection = AsyncMock()
        return collection
    
    @pytest.fixture
    def repository(self, mock_database, mock_collection):
        """Create a test repository instance."""
        mock_database.__getitem__ = Mock(return_value=mock_collection)
        repo = TestRepository(mock_database, TestModel)
        return repo
    
    def test_repository_initialization(self, mock_database, mock_collection):
        """Test repository initialization."""
        # Configure mock to return collection when accessed by name
        mock_database.__getitem__ = Mock(return_value=mock_collection)
        
        repo = TestRepository(mock_database, TestModel)
        
        assert repo.database == mock_database
        assert repo.model_class == TestModel
        assert repo.collection_name == "test_collection"
        assert repo.collection == mock_collection
    
    @pytest.mark.asyncio
    async def test_create_document_success(self, repository, mock_collection):
        """Test successful document creation."""
        # Setup
        test_doc = TestModel(name="test", value=42)
        mock_inserted_id = ObjectId()
        
        # Mock the insert_one call
        mock_result = Mock()
        mock_result.inserted_id = mock_inserted_id
        mock_collection.insert_one.return_value = mock_result
        
        # Mock the find_by_id call (via find_one)
        created_doc_data = {
            "_id": mock_inserted_id,
            "name": "test", 
            "value": 42
        }
        mock_collection.find_one.return_value = created_doc_data
        
        # Execute
        result = await repository.create(test_doc)
        
        # Verify
        assert result.name == "test"
        assert result.value == 42
        mock_collection.insert_one.assert_called_once()
        mock_collection.find_one.assert_called_once_with({"_id": mock_inserted_id})
    
    @pytest.mark.asyncio
    async def test_find_by_id_success(self, repository, mock_collection):
        """Test successful find by ID."""
        # Setup
        test_id = ObjectId()
        mock_doc_data = {
            "_id": test_id,
            "name": "found_doc",
            "value": 100
        }
        mock_collection.find_one.return_value = mock_doc_data
        
        # Execute
        result = await repository.find_by_id(test_id)
        
        # Verify
        assert result is not None
        assert result.name == "found_doc"
        assert result.value == 100
        mock_collection.find_one.assert_called_once_with({"_id": test_id})
    
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository, mock_collection):
        """Test find by ID when document doesn't exist."""
        # Setup
        test_id = ObjectId()
        mock_collection.find_one.return_value = None
        
        # Execute
        result = await repository.find_by_id(test_id)
        
        # Verify
        assert result is None
        mock_collection.find_one.assert_called_once_with({"_id": test_id})
    
    @pytest.mark.asyncio
    async def test_create_document_insertion_failure(self, repository, mock_collection):
        """Test document creation when insertion fails."""
        # Setup
        test_doc = TestModel(name="test", value=42)
        mock_collection.insert_one.side_effect = Exception("Database error")
        
        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await repository.create(test_doc)
    
    @pytest.mark.asyncio
    async def test_find_by_id_database_error(self, repository, mock_collection):
        """Test find by ID when database error occurs."""
        # Setup
        test_id = ObjectId()
        mock_collection.find_one.side_effect = Exception("Database connection error")
        
        # Execute and verify exception
        with pytest.raises(Exception, match="Database connection error"):
            await repository.find_by_id(test_id)


class TestBaseRepositoryPatterns:
    """Test repository patterns and behaviors."""
    
    def test_abstract_method_enforcement(self):
        """Test that _get_collection_name must be implemented."""
        # This tests that BaseRepository is abstract
        with pytest.raises(TypeError):
            # Should not be able to instantiate BaseRepository directly
            BaseRepository(Mock(), TestModel)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
