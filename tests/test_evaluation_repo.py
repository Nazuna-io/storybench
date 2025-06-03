"""Test evaluation repository."""

import pytest
from unittest.mock import Mock, AsyncMock
from bson import ObjectId

from src.storybench.database.repositories.evaluation_repo import EvaluationRepository


class TestEvaluationRepository:
    """Test EvaluationRepository functionality."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        return Mock()
    
    @pytest.fixture
    def evaluation_repo(self, mock_database):
        """Create EvaluationRepository with mocked dependencies."""
        with pytest.MonkeyPatch().context() as m:
            # Mock the base repository initialization
            m.setattr('src.storybench.database.repositories.evaluation_repo.BaseRepository.__init__', 
                     lambda self, db, model_class: None)
            
            repo = EvaluationRepository(mock_database)
            repo.collection = Mock()  # Mock the collection
            return repo
    
    def test_initialization(self, mock_database):
        """Test EvaluationRepository initialization."""
        with pytest.MonkeyPatch().context() as m:
            m.setattr('src.storybench.database.repositories.evaluation_repo.BaseRepository.__init__', 
                     lambda self, db, model_class: None)
            
            repo = EvaluationRepository(mock_database)
            assert repo is not None
    
    def test_get_collection_name(self, evaluation_repo):
        """Test collection name method."""
        assert evaluation_repo._get_collection_name() == "evaluations"
    
    @pytest.mark.asyncio
    async def test_find_by_config_hash(self, evaluation_repo):
        """Test finding evaluations by config hash."""
        # Mock collection.find method
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": ObjectId(), "config_hash": "abc123", "status": "completed"},
            {"_id": ObjectId(), "config_hash": "abc123", "status": "running"}
        ])
        evaluation_repo.collection.find.return_value = mock_cursor
        
        # Mock Evaluation.from_mongo method
        with pytest.MonkeyPatch().context() as m:
            mock_evaluation1 = Mock()
            mock_evaluation2 = Mock()
            
            def mock_from_mongo(doc):
                if doc["status"] == "completed":
                    return mock_evaluation1
                else:
                    return mock_evaluation2
            
            m.setattr('src.storybench.database.repositories.evaluation_repo.Evaluation.from_mongo', 
                     mock_from_mongo)
            
            result = await evaluation_repo.find_by_config_hash("abc123")
            
            evaluation_repo.collection.find.assert_called_once_with({"config_hash": "abc123"})
            assert len(result) == 2
