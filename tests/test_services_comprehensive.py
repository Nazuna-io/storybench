"""Comprehensive database services tests for major coverage boost."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.database.services.config_service import ConfigService
from storybench.database.services.evaluation_service import EvaluationService


class TestConfigService:
    """Comprehensive ConfigService tests."""
    
    @pytest.fixture
    def mock_repo(self):
        """Mock repository."""
        mock = Mock()
        mock.find_all = AsyncMock()
        mock.find_by_id = AsyncMock()
        mock.create = AsyncMock()
        mock.update = AsyncMock()
        return mock
        
    @pytest.fixture
    def config_service(self, mock_repo):
        """ConfigService fixture."""
        return ConfigService(mock_repo)
        
    async def test_get_all_models(self, config_service, mock_repo):
        """Test get_all_models method."""
        mock_repo.find_all.return_value = [
            {"id": 1, "name": "model1", "enabled": True},
            {"id": 2, "name": "model2", "enabled": False}
        ]
        
        result = await config_service.get_all_models()
        
        assert len(result) == 2
        mock_repo.find_all.assert_called_once()
        
    async def test_get_enabled_models_only(self, config_service, mock_repo):
        """Test filtering enabled models."""
        mock_repo.find_all.return_value = [
            {"id": 1, "name": "model1", "enabled": True},
            {"id": 2, "name": "model2", "enabled": False},
            {"id": 3, "name": "model3", "enabled": True}
        ]
        
        result = await config_service.get_enabled_models()
        
        # Should return only enabled models
        assert all(model.get("enabled", False) for model in result if "enabled" in model)
        mock_repo.find_all.assert_called_once()
        
    async def test_get_model_by_id(self, config_service, mock_repo):
        """Test get_model_by_id method."""
        mock_repo.find_by_id.return_value = {"id": 1, "name": "test-model"}
        
        result = await config_service.get_model_by_id(1)
        
        assert result["id"] == 1
        assert result["name"] == "test-model"
        mock_repo.find_by_id.assert_called_once_with(1)
        
    async def test_create_model_config(self, config_service, mock_repo):
        """Test create_model_config method."""
        model_data = {
            "name": "new-model",
            "provider": "openai",
            "enabled": True
        }
        
        mock_repo.create.return_value = {"id": 1, **model_data}
        
        result = await config_service.create_model_config(model_data)
        
        assert result["id"] == 1
        assert result["name"] == "new-model"
        mock_repo.create.assert_called_once_with(model_data)
        
    async def test_update_model_config(self, config_service, mock_repo):
        """Test update_model_config method."""
        update_data = {"enabled": False}
        mock_repo.update.return_value = {"id": 1, "name": "model", "enabled": False}
        
        result = await config_service.update_model_config(1, update_data)
        
        assert result["enabled"] is False
        mock_repo.update.assert_called_once_with(1, update_data)


class TestEvaluationService:
    """Comprehensive EvaluationService tests."""
    
    @pytest.fixture
    def mock_eval_repo(self):
        """Mock evaluation repository."""
        mock = Mock()
        mock.find_all = AsyncMock()
        mock.find_by_id = AsyncMock()
        mock.create = AsyncMock()
        mock.update = AsyncMock()
        mock.find_by_status = AsyncMock()
        return mock
        
    @pytest.fixture
    def evaluation_service(self, mock_eval_repo):
        """EvaluationService fixture."""
        return EvaluationService(mock_eval_repo)
        
    async def test_create_evaluation(self, evaluation_service, mock_eval_repo):
        """Test create_evaluation method."""
        eval_data = {
            "model_id": 1,
            "prompt_id": 1,
            "status": "pending"
        }
        
        mock_eval_repo.create.return_value = {"id": 1, **eval_data}
        
        result = await evaluation_service.create_evaluation(eval_data)
        
        assert result["id"] == 1
        assert result["status"] == "pending"
        mock_eval_repo.create.assert_called_once_with(eval_data)
        
    async def test_get_evaluation_by_id(self, evaluation_service, mock_eval_repo):
        """Test get_evaluation_by_id method."""
        mock_eval_repo.find_by_id.return_value = {
            "id": 1, "model_id": 1, "prompt_id": 1, "status": "completed"
        }
        
        result = await evaluation_service.get_evaluation_by_id(1)
        
        assert result["id"] == 1
        assert result["status"] == "completed"
        mock_eval_repo.find_by_id.assert_called_once_with(1)
        
    async def test_get_evaluations_by_status(self, evaluation_service, mock_eval_repo):
        """Test get_evaluations_by_status method."""
        mock_eval_repo.find_by_status.return_value = [
            {"id": 1, "status": "pending"},
            {"id": 2, "status": "pending"}
        ]
        
        result = await evaluation_service.get_evaluations_by_status("pending")
        
        assert len(result) == 2
        assert all(eval["status"] == "pending" for eval in result)
        mock_eval_repo.find_by_status.assert_called_once_with("pending")
