"""
Comprehensive tests for database services to improve coverage.
Tests sequence evaluation, LLM evaluation, and evaluation runner services.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from src.storybench.database.services.sequence_evaluation_service import SequenceEvaluationService
from src.storybench.database.services.llm_evaluation_service import LLMEvaluationService
from src.storybench.database.services.evaluation_runner import EvaluationRunner
from src.storybench.database.models import (
    Evaluation, Response, EvaluationScore, 
    SequenceEvaluationScore, ResponseLLMEvaluation
)
from src.storybench.models.config import EvaluationConfig


class TestSequenceEvaluationService:
    """Test the SequenceEvaluationService class."""
    
    @pytest.fixture
    def mock_evaluation_repo(self):
        """Mock evaluation repository."""
        return Mock()
    
    @pytest.fixture
    def mock_response_repo(self):
        """Mock response repository."""
        return Mock()
    
    @pytest.fixture
    def mock_score_repo(self):
        """Mock evaluation score repository.""" 
        return Mock()
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_evaluation_repo, mock_response_repo, mock_score_repo, mock_openai_client):
        """Create SequenceEvaluationService instance."""
        return SequenceEvaluationService(
            evaluation_repo=mock_evaluation_repo,
            response_repo=mock_response_repo,
            evaluation_score_repo=mock_score_repo,
            openai_client=mock_openai_client
        )
    
    @pytest.fixture
    def sample_evaluation(self):
        """Sample evaluation for testing."""
        return Evaluation(
            id=ObjectId(),
            config_hash="test_hash",
            models=["GPT-4o", "Claude-4-Sonnet"],
            status="completed",
            total_tasks=4,
            completed_tasks=4,
            timestamp=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_responses(self):
        """Sample responses for testing."""
        eval_id = ObjectId()
        return [
            Response(
                id=ObjectId(),
                evaluation_id=str(eval_id),
                model_name="GPT-4o",
                sequence="FilmNarrative",
                run=1,
                prompt_name="Initial Concept",
                response="A sci-fi thriller about AI consciousness.",
                generation_time=2.5,
                completed_at=datetime.now(timezone.utc)
            ),
            Response(
                id=ObjectId(),
                evaluation_id=str(eval_id),
                model_name="GPT-4o", 
                sequence="FilmNarrative",
                run=1,
                prompt_name="Character Development",
                response="The protagonist is Dr. Sarah Chen, an AI researcher.",
                generation_time=3.2,
                completed_at=datetime.now(timezone.utc)
            )
        ]
