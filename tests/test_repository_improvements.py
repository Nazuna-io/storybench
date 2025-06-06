"""Test database repository improvements."""

import pytest
from unittest.mock import Mock, AsyncMock

from src.storybench.database.repositories.criteria_repo import CriteriaRepository
from src.storybench.database.repositories.model_repo import ModelRepository
from src.storybench.database.repositories.prompt_repo import PromptRepository


class TestRepositoryImprovements:
    """Test repository classes with mocked database."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        db = Mock()
        db.criteria = Mock()
        db.models = Mock()
        db.prompts = Mock()
        return db
    
    def test_criteria_repository_init(self, mock_database):
        """Test criteria repository initialization."""
        repo = CriteriaRepository(mock_database)
        assert repo.db == mock_database
        assert repo.collection == mock_database.criteria
    
    def test_model_repository_init(self, mock_database):
        """Test model repository initialization."""
        repo = ModelRepository(mock_database)
        assert repo.db == mock_database
        assert repo.collection == mock_database.models
    
    def test_prompt_repository_init(self, mock_database):
        """Test prompt repository initialization."""
        repo = PromptRepository(mock_database)
        assert repo.db == mock_database
        assert repo.collection == mock_database.prompts
    
    @pytest.mark.asyncio
    async def test_criteria_repository_get_all(self, mock_database):
        """Test getting all criteria."""
        mock_database.criteria.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "1", "name": "coherence"}]
        )
        
        repo = CriteriaRepository(mock_database)
        result = await repo.get_all()
        
        assert len(result) == 1
        assert result[0]["name"] == "coherence"
