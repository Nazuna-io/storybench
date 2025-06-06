"""Additional database tests for coverage boost."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.database.models import Evaluation, Model, Prompt, Response
from storybench.database.connection import DatabaseConnection
from unittest.mock import Mock, AsyncMock, patch


class TestDatabaseModelsExtended:
    """Extended database model tests."""
    
    def test_evaluation_model_with_all_fields(self):
        """Test Evaluation model with all fields."""
        evaluation = Evaluation(
            id=1,
            model_id=1,
            prompt_id=1,
            status="completed",
            created_at="2024-01-01T00:00:00",
            completed_at="2024-01-01T00:05:00",
            error_message=None
        )
        
        assert evaluation.id == 1
        assert evaluation.model_id == 1
        assert evaluation.prompt_id == 1
        assert evaluation.status == "completed"
        assert evaluation.created_at == "2024-01-01T00:00:00"
        assert evaluation.completed_at == "2024-01-01T00:05:00"
        assert evaluation.error_message is None
        
    def test_model_with_all_fields(self):
        """Test Model with all fields."""
        model = Model(
            id=1,
            name="test-model",
            provider="openai",
            api_base="https://api.openai.com/v1",
            enabled=True,
            max_tokens=2048,
            temperature=0.7
        )
        
        assert model.id == 1
        assert model.name == "test-model"
        assert model.provider == "openai"
        assert model.api_base == "https://api.openai.com/v1"
        assert model.enabled is True
        assert model.max_tokens == 2048
        assert model.temperature == 0.7
        
    def test_prompt_with_variables(self):
        """Test Prompt with template variables."""
        prompt = Prompt(
            id=1,
            name="test-prompt",
            content="Tell me about {topic} in {style} style",
            system_prompt="You are a helpful assistant"
        )
        
        assert prompt.id == 1
        assert prompt.name == "test-prompt"
        assert "{topic}" in prompt.content
        assert "{style}" in prompt.content
        assert prompt.system_prompt == "You are a helpful assistant"
        
    def test_response_with_metadata(self):
        """Test Response with metadata."""
        response = Response(
            id=1,
            evaluation_id=1,
            response_text="This is a test response",
            tokens_used=150,
            response_time=2.5,
            created_at="2024-01-01T00:00:00"
        )
        
        assert response.id == 1
        assert response.evaluation_id == 1
        assert response.response_text == "This is a test response"
        assert response.tokens_used == 150
        assert response.response_time == 2.5
        assert response.created_at == "2024-01-01T00:00:00"


class TestDatabaseConnectionExtended:
    """Extended database connection tests."""
    
    @pytest.fixture
    def mock_asyncpg(self):
        """Mock asyncpg module."""
        with patch('storybench.database.connection.asyncpg') as mock:
            yield mock
    
    def test_database_connection_init(self, mock_asyncpg):
        """Test DatabaseConnection initialization."""
        db = DatabaseConnection("postgresql://user:pass@host:5432/db")
        
        assert db.connection_string == "postgresql://user:pass@host:5432/db"
        assert db.pool is None
