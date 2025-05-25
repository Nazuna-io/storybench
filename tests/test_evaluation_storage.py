"""Test evaluation storage and database operations."""

import pytest
from unittest.mock import AsyncMock
from bson import ObjectId

from storybench.database.services.evaluation_runner import DatabaseEvaluationRunner
from storybench.database.models import Evaluation, EvaluationStatus, GlobalSettings

class TestEvaluationStorage:
    """Test evaluation storage functionality."""
    
    @pytest.fixture
    def evaluation_runner(self):
        """Create evaluation runner with mocked database."""
        mock_database = AsyncMock()
        return DatabaseEvaluationRunner(mock_database)
        
    @pytest.mark.asyncio
    async def test_total_tasks_calculation(self, evaluation_runner):
        """Test calculation of total tasks."""
        models = ["model1", "model2"]
        sequences = {
            "seq1": [{"name": "p1", "text": "..."}, {"name": "p2", "text": "..."}],
            "seq2": [{"name": "p3", "text": "..."}]
        }
        num_runs = 3
        
        total = evaluation_runner._calculate_total_tasks(models, sequences, num_runs)
        # 2 models * 3 prompts total * 3 runs = 18
        assert total == 18
        
    @pytest.mark.asyncio
    async def test_evaluation_runner_initialization(self, evaluation_runner):
        """Test evaluation runner initialization."""
        assert evaluation_runner.database is not None
        assert evaluation_runner.evaluation_repo is not None
        assert evaluation_runner.response_repo is not None
        assert evaluation_runner.config_service is not None
