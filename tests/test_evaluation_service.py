"""
Comprehensive tests for database/services/evaluation_service.py
These tests cover the EvaluationService with mocked repositories.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bson import ObjectId
from datetime import datetime

# Import the service we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestEvaluationService:
    """Test the EvaluationService class."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        return Mock()
    
    @patch('storybench.database.services.evaluation_service.EvaluationRepository')
    @patch('storybench.database.services.evaluation_service.ResponseRepository')
    def test_evaluation_service_initialization(self, mock_response_repo, mock_eval_repo, mock_database):
        """Test evaluation service initialization."""
        from storybench.database.services.evaluation_service import EvaluationService
        
        service = EvaluationService(mock_database)
        
        assert service.database == mock_database
        mock_eval_repo.assert_called_once_with(mock_database)
        mock_response_repo.assert_called_once_with(mock_database)
    
    @patch('storybench.database.services.evaluation_service.EvaluationRepository')
    @patch('storybench.database.services.evaluation_service.ResponseRepository')
    @patch('storybench.database.services.evaluation_service.Evaluation')
    @pytest.mark.asyncio
    async def test_create_evaluation(self, mock_evaluation_class, mock_response_repo, mock_eval_repo, mock_database):
        """Test creating a new evaluation."""
        from storybench.database.services.evaluation_service import EvaluationService
        from storybench.database.models import GlobalSettings, EvaluationStatus
        
        # Setup mocks
        mock_evaluation_instance = Mock()
        mock_evaluation_class.return_value = mock_evaluation_instance
        
        mock_eval_repo_instance = AsyncMock()
        mock_created_evaluation = Mock()
        mock_eval_repo_instance.create.return_value = mock_created_evaluation
        mock_eval_repo.return_value = mock_eval_repo_instance
        
        mock_response_repo.return_value = AsyncMock()
        
        service = EvaluationService(mock_database)
        
        # Test data
        config_hash = "test_hash_123"
        models = ["gpt-4", "claude-3"]
        global_settings = GlobalSettings(temperature=0.7, max_tokens=1000, num_runs=3, vram_limit_percent=80)
        total_tasks = 50
        
        # Execute
        result = await service.create_evaluation(config_hash, models, global_settings, total_tasks)
        
        # Verify
        assert result == mock_created_evaluation
        mock_evaluation_class.assert_called_once()
        call_kwargs = mock_evaluation_class.call_args[1]
        assert call_kwargs['config_hash'] == config_hash
        assert call_kwargs['models'] == models
        assert call_kwargs['global_settings'] == global_settings
        assert call_kwargs['total_tasks'] == total_tasks
        assert call_kwargs['status'] == EvaluationStatus.IN_PROGRESS
        
        mock_eval_repo_instance.create.assert_called_once_with(mock_evaluation_instance)
    
    @patch('storybench.database.services.evaluation_service.EvaluationRepository')
    @patch('storybench.database.services.evaluation_service.ResponseRepository')
    @pytest.mark.asyncio
    async def test_find_incomplete_evaluations(self, mock_response_repo, mock_eval_repo, mock_database):
        """Test finding incomplete evaluations."""
        from storybench.database.services.evaluation_service import EvaluationService
        
        # Setup mocks
        mock_eval_repo_instance = AsyncMock()
        mock_incomplete_evaluations = [Mock(), Mock()]
        mock_eval_repo_instance.find_incomplete.return_value = mock_incomplete_evaluations
        mock_eval_repo.return_value = mock_eval_repo_instance
        
        mock_response_repo.return_value = AsyncMock()
        
        service = EvaluationService(mock_database)
        
        # Execute
        result = await service.find_incomplete_evaluations()
        
        # Verify
        assert result == mock_incomplete_evaluations
        mock_eval_repo_instance.find_incomplete.assert_called_once()
    
    @patch('storybench.database.services.evaluation_service.EvaluationRepository')
    @patch('storybench.database.services.evaluation_service.ResponseRepository')
    @pytest.mark.asyncio
    async def test_get_evaluation_progress(self, mock_response_repo, mock_eval_repo, mock_database):
        """Test getting evaluation progress."""
        from storybench.database.services.evaluation_service import EvaluationService
        
        # Setup mocks
        evaluation_id = ObjectId()
        
        mock_eval_repo_instance = AsyncMock()
        mock_evaluation = Mock()
        mock_evaluation.total_tasks = 100
        mock_eval_repo_instance.find_by_id.return_value = mock_evaluation
        mock_eval_repo.return_value = mock_eval_repo_instance
        
        mock_response_repo_instance = AsyncMock()
        mock_response_repo_instance.count_by_evaluation.return_value = 75
        mock_response_repo.return_value = mock_response_repo_instance
        
        service = EvaluationService(mock_database)
        
        # Execute  
        result = await service.get_evaluation_progress(evaluation_id)
        
        # Verify
        assert isinstance(result, dict)
        mock_eval_repo_instance.find_by_id.assert_called_once_with(evaluation_id)
        mock_response_repo_instance.count_by_evaluation.assert_called_once_with(evaluation_id)


class TestEvaluationServiceErrorHandling:
    """Test error handling in evaluation service."""
    
    @patch('storybench.database.services.evaluation_service.EvaluationRepository')
    @patch('storybench.database.services.evaluation_service.ResponseRepository')
    @pytest.mark.asyncio
    async def test_find_incomplete_evaluations_empty_result(self, mock_response_repo, mock_eval_repo, mock_database):
        """Test finding incomplete evaluations when none exist."""
        from storybench.database.services.evaluation_service import EvaluationService
        
        mock_eval_repo_instance = AsyncMock()
        mock_eval_repo_instance.find_incomplete.return_value = []
        mock_eval_repo.return_value = mock_eval_repo_instance
        
        mock_response_repo.return_value = AsyncMock()
        
        service = EvaluationService(mock_database)
        
        result = await service.find_incomplete_evaluations()
        
        assert result == []
        mock_eval_repo_instance.find_incomplete.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
