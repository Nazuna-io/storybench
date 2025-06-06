"""Enhanced repository tests for coverage boost."""

import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.database.repositories.api_keys_repo import APIKeysRepository
from storybench.database.repositories.response_repo import ResponseRepository
from storybench.database.repositories.response_llm_evaluation_repository import ResponseLLMEvaluationRepository


class TestAPIKeysRepository:
    """Comprehensive APIKeysRepository tests."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        mock = Mock()
        mock.execute = AsyncMock()
        mock.fetch = AsyncMock()
        mock.fetchrow = AsyncMock()
        return mock
        
    @pytest.fixture
    def api_keys_repo(self, mock_db):
        """APIKeysRepository fixture."""
        return APIKeysRepository(mock_db)
        
    async def test_find_all_api_keys(self, api_keys_repo, mock_db):
        """Test find_all method."""
        mock_db.fetch.return_value = [
            {"id": 1, "provider": "openai", "key_name": "main", "masked_key": "sk-***"},
            {"id": 2, "provider": "anthropic", "key_name": "backup", "masked_key": "sk-ant-***"}
        ]
        
        result = await api_keys_repo.find_all()
        
        assert len(result) == 2
        assert result[0]["provider"] == "openai"
        assert result[1]["provider"] == "anthropic"
        mock_db.fetch.assert_called_once()
        
    async def test_find_by_provider(self, api_keys_repo, mock_db):
        """Test find_by_provider method."""
        mock_db.fetch.return_value = [
            {"id": 1, "provider": "openai", "key_name": "main"}
        ]
        
        result = await api_keys_repo.find_by_provider("openai")
        
        assert len(result) == 1
        assert result[0]["provider"] == "openai"
        mock_db.fetch.assert_called_once()
        
    async def test_create_api_key(self, api_keys_repo, mock_db):
        """Test create method."""
        key_data = {
            "provider": "openai",
            "key_name": "test",
            "encrypted_key": "encrypted_value",
            "masked_key": "sk-***"
        }
        
        mock_db.fetchrow.return_value = {"id": 1, **key_data}
        
        result = await api_keys_repo.create(key_data)
        
        assert result["id"] == 1
        assert result["provider"] == "openai"
        mock_db.fetchrow.assert_called_once()
        
    async def test_update_api_key(self, api_keys_repo, mock_db):
        """Test update method."""
        update_data = {"key_name": "updated_name"}
        mock_db.fetchrow.return_value = {"id": 1, "key_name": "updated_name"}
        
        result = await api_keys_repo.update(1, update_data)
        
        assert result["key_name"] == "updated_name"
        mock_db.fetchrow.assert_called_once()
        
    async def test_delete_api_key(self, api_keys_repo, mock_db):
        """Test delete method."""
        mock_db.execute.return_value = None
        
        await api_keys_repo.delete(1)
        
        mock_db.execute.assert_called_once()


class TestResponseRepository:
    """Comprehensive ResponseRepository tests."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        mock = Mock()
        mock.execute = AsyncMock()
        mock.fetch = AsyncMock()
        mock.fetchrow = AsyncMock()
        return mock
        
    @pytest.fixture
    def response_repo(self, mock_db):
        """ResponseRepository fixture."""
        return ResponseRepository(mock_db)
        
    async def test_find_by_evaluation_id(self, response_repo, mock_db):
        """Test find_by_evaluation_id method."""
        mock_db.fetch.return_value = [
            {"id": 1, "evaluation_id": 1, "response_text": "Test response", "tokens_used": 100},
            {"id": 2, "evaluation_id": 1, "response_text": "Another response", "tokens_used": 150}
        ]
        
        result = await response_repo.find_by_evaluation_id(1)
        
        assert len(result) == 2
        assert all(resp["evaluation_id"] == 1 for resp in result)
        mock_db.fetch.assert_called_once()
        
    async def test_create_response(self, response_repo, mock_db):
        """Test create response method."""
        response_data = {
            "evaluation_id": 1,
            "response_text": "Generated response",
            "tokens_used": 200,
            "response_time": 1.5
        }
        
        mock_db.fetchrow.return_value = {"id": 1, **response_data}
        
        result = await response_repo.create(response_data)
        
        assert result["id"] == 1
        assert result["response_text"] == "Generated response"
        assert result["tokens_used"] == 200
        mock_db.fetchrow.assert_called_once()
        
    async def test_get_response_stats(self, response_repo, mock_db):
        """Test getting response statistics."""
        mock_db.fetchrow.return_value = {
            "total_responses": 100,
            "avg_tokens": 150.5,
            "avg_response_time": 2.3
        }
        
        result = await response_repo.get_stats()
        
        assert result["total_responses"] == 100
        assert result["avg_tokens"] == 150.5
        mock_db.fetchrow.assert_called_once()


class TestResponseLLMEvaluationRepository:
    """Test ResponseLLMEvaluationRepository."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        mock = Mock()
        mock.execute = AsyncMock()
        mock.fetch = AsyncMock()
        mock.fetchrow = AsyncMock()
        return mock
        
    @pytest.fixture
    def llm_eval_repo(self, mock_db):
        """ResponseLLMEvaluationRepository fixture."""
        return ResponseLLMEvaluationRepository(mock_db)
        
    async def test_find_by_response_id(self, llm_eval_repo, mock_db):
        """Test find_by_response_id method."""
        mock_db.fetch.return_value = [
            {"id": 1, "response_id": 1, "criteria_id": 1, "score": 4.5},
            {"id": 2, "response_id": 1, "criteria_id": 2, "score": 3.8}
        ]
        
        result = await llm_eval_repo.find_by_response_id(1)
        
        assert len(result) == 2
        assert all(eval["response_id"] == 1 for eval in result)
        mock_db.fetch.assert_called_once()
