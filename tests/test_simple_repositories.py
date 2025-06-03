"""Test simple repository methods."""

import pytest
from unittest.mock import Mock, AsyncMock

from src.storybench.database.repositories.criteria_repo import CriteriaRepository
from src.storybench.database.repositories.model_repo import ModelRepository
from src.storybench.database.repositories.prompt_repo import PromptRepository


class TestSimpleRepositories:
    """Test simple repository functionality without complex dependencies."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        return Mock()
    
    def test_criteria_repo_collection_name(self):
        """Test CriteriaRepository collection name."""
        with pytest.MonkeyPatch().context() as m:
            # Mock the base repository initialization
            m.setattr('src.storybench.database.repositories.criteria_repo.BaseRepository.__init__', 
                     lambda self, db, model_class: None)
            
            repo = CriteriaRepository(Mock())
            assert repo._get_collection_name() == "evaluation_criteria"
    
    def test_model_repo_collection_name(self):
        """Test ModelRepository collection name."""
        with pytest.MonkeyPatch().context() as m:
            # Mock the base repository initialization
            m.setattr('src.storybench.database.repositories.model_repo.BaseRepository.__init__', 
                     lambda self, db, model_class: None)
            
            repo = ModelRepository(Mock())
            assert repo._get_collection_name() == "models"
    
    def test_prompt_repo_collection_name(self):
        """Test PromptRepository collection name."""
        with pytest.MonkeyPatch().context() as m:
            # Mock the base repository initialization
            m.setattr('src.storybench.database.repositories.prompt_repo.BaseRepository.__init__', 
                     lambda self, db, model_class: None)
            
            repo = PromptRepository(Mock())
            assert repo._get_collection_name() == "prompts"
    
    @pytest.mark.asyncio
    async def test_criteria_repo_get_all(self):
        """Test CriteriaRepository get_all method."""
        with pytest.MonkeyPatch().context() as m:
            # Mock the base repository initialization
            m.setattr('src.storybench.database.repositories.criteria_repo.BaseRepository.__init__', 
                     lambda self, db, model_class: None)
            
            repo = CriteriaRepository(Mock())
            repo.collection = Mock()
            
            # Mock collection.find method
            mock_cursor = Mock()
            mock_cursor.to_list = AsyncMock(return_value=[
                {"_id": "1", "name": "creativity", "description": "Test creativity"}
            ])
            repo.collection.find.return_value = mock_cursor
            
            # Mock the model's from_mongo method
            m.setattr('src.storybench.database.repositories.criteria_repo.EvaluationCriteria.from_mongo', 
                     lambda doc: doc)
            
            result = await repo.get_all()
            
            # Verify collection.find was called with empty filter
            repo.collection.find.assert_called_once_with({})
            assert len(result) == 1
            assert result[0]["name"] == "creativity"
