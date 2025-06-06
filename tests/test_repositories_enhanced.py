"""Enhanced repository tests for better coverage."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.database.repositories.base import BaseRepository
from storybench.database.repositories.criteria_repo import CriteriaRepository
from storybench.database.repositories.model_repo import ModelRepository
from storybench.database.repositories.prompt_repo import PromptRepository
from storybench.database.repositories.evaluation_repo import EvaluationRepository
from storybench.database.repositories.response_repo import ResponseRepository
from storybench.database.models import Criteria, Model, Prompt, Evaluation, Response
from pydantic import BaseModel


class TestRepositoryMethods:
    """Test repository method coverage."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        mock_db = Mock()
        mock_db.execute = AsyncMock()
        mock_db.fetch = AsyncMock()
        mock_db.fetchrow = AsyncMock() 
        return mock_db
        
    @pytest.fixture
    def criteria_repo(self, mock_db):
        """Criteria repository fixture."""
        return CriteriaRepository(mock_db)
        
    @pytest.fixture
    def model_repo(self, mock_db):
        """Model repository fixture."""
        return ModelRepository(mock_db)
        
    @pytest.fixture
    def prompt_repo(self, mock_db):
        """Prompt repository fixture."""
        return PromptRepository(mock_db)
        
    @pytest.fixture
    def evaluation_repo(self, mock_db):
        """Evaluation repository fixture."""
        return EvaluationRepository(mock_db)
        
    @pytest.fixture
    def response_repo(self, mock_db):
        """Response repository fixture."""
        return ResponseRepository(mock_db)
        
    async def test_criteria_repo_find_all(self, criteria_repo, mock_db):
        """Test criteria repository find_all method."""
        mock_db.fetch.return_value = [
            {"id": 1, "name": "test", "description": "test", "weight": 1.0}
        ]
        
        result = await criteria_repo.find_all()
        
        assert len(result) == 1
        mock_db.fetch.assert_called_once()
        
    async def test_model_repo_find_all(self, model_repo, mock_db):
        """Test model repository find_all method."""
        mock_db.fetch.return_value = [
            {"id": 1, "name": "test", "provider": "test", "api_base": "test", "enabled": True}
        ]
        
        result = await model_repo.find_all()
        
        assert len(result) == 1
        mock_db.fetch.assert_called_once()
        
    async def test_prompt_repo_find_all(self, prompt_repo, mock_db):
        """Test prompt repository find_all method.""" 
        mock_db.fetch.return_value = [
            {"id": 1, "name": "test", "content": "test", "system_prompt": "test"}
        ]
        
        result = await prompt_repo.find_all()
        
        assert len(result) == 1
        mock_db.fetch.assert_called_once()
        
    async def test_evaluation_repo_find_by_status(self, evaluation_repo, mock_db):
        """Test evaluation repository find_by_status method."""
        mock_db.fetch.return_value = [
            {"id": 1, "model_id": 1, "prompt_id": 1, "status": "completed"}
        ]
        
        result = await evaluation_repo.find_by_status("completed")
        
        assert len(result) == 1
        mock_db.fetch.assert_called_once()
        
    async def test_response_repo_find_by_evaluation_id(self, response_repo, mock_db):
        """Test response repository find_by_evaluation_id method."""
        mock_db.fetch.return_value = [
            {"id": 1, "evaluation_id": 1, "response_text": "test", "tokens_used": 100}
        ]
        
        result = await response_repo.find_by_evaluation_id(1)
        
        assert len(result) == 1
        mock_db.fetch.assert_called_once()
