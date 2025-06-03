"""Test web models - requests and responses."""

import pytest
from pydantic import ValidationError
from datetime import datetime

from src.storybench.web.models.requests import (
    ModelConfigRequest,
    GlobalSettingsRequest,
    EvaluationConfigRequest
)

from src.storybench.web.models.responses import (
    ModelConfigResponse,
    GlobalSettingsResponse,
    EvaluationConfigResponse
)


class TestRequestModels:
    """Test request model validation."""
    
    def test_model_config_request_valid(self):
        """Test valid ModelConfigRequest."""
        data = {
            "name": "gpt-4",
            "type": "api",
            "provider": "openai",
            "model_name": "gpt-4-turbo"
        }
        
        model = ModelConfigRequest(**data)
        assert model.name == "gpt-4"
        assert model.type == "api"
        assert model.provider == "openai"
        assert model.model_name == "gpt-4-turbo"
        assert model.repo_id is None
        assert model.filename is None
        assert model.subdirectory is None
    
    def test_model_config_request_local_model(self):
        """Test ModelConfigRequest for local model."""
        data = {
            "name": "llama-3",
            "type": "local",
            "model_name": "llama-3-8b",
            "repo_id": "meta-llama/llama-3-8b",
            "filename": "model.gguf",
            "subdirectory": "models"
        }
        
        model = ModelConfigRequest(**data)
        assert model.name == "llama-3"
        assert model.type == "local"
        assert model.provider is None
        assert model.repo_id == "meta-llama/llama-3-8b"
        assert model.filename == "model.gguf"
        assert model.subdirectory == "models"

    def test_model_config_request_invalid_type(self):
        """Test ModelConfigRequest with invalid type."""
        data = {
            "name": "test",
            "type": "invalid",
            "model_name": "test-model"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ModelConfigRequest(**data)
        
        assert "type" in str(exc_info.value)
    
    def test_model_config_request_missing_required(self):
        """Test ModelConfigRequest with missing required fields."""
        data = {
            "name": "test"
            # Missing type and model_name
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ModelConfigRequest(**data)
        
        errors = exc_info.value.errors()
        field_names = [error['loc'][0] for error in errors]
        assert 'type' in field_names
        assert 'model_name' in field_names
    
    def test_global_settings_request_valid(self):
        """Test valid GlobalSettingsRequest."""
        data = {
            "temperature": 0.7,
            "max_tokens": 2048,
            "num_runs": 5,
            "vram_limit_percent": 85
        }
        
        settings = GlobalSettingsRequest(**data)
        assert settings.temperature == 0.7
        assert settings.max_tokens == 2048
        assert settings.num_runs == 5
        assert settings.vram_limit_percent == 85
    
    def test_global_settings_request_defaults(self):
        """Test GlobalSettingsRequest with default values."""
        settings = GlobalSettingsRequest()
        assert settings.temperature == 0.9
        assert settings.max_tokens == 4096
        assert settings.num_runs == 3
        assert settings.vram_limit_percent == 80
    
    def test_global_settings_request_validation(self):
        """Test GlobalSettingsRequest validation bounds."""
        # Test temperature out of bounds
        with pytest.raises(ValidationError):
            GlobalSettingsRequest(temperature=3.0)
        
        # Test max_tokens out of bounds
        with pytest.raises(ValidationError):
            GlobalSettingsRequest(max_tokens=0)
        
        # Test num_runs out of bounds
        with pytest.raises(ValidationError):
            GlobalSettingsRequest(num_runs=15)
        
        # Test vram_limit_percent out of bounds
        with pytest.raises(ValidationError):
            GlobalSettingsRequest(vram_limit_percent=5)


class TestResponseModels:
    """Test response model functionality."""
    
    def test_model_config_response(self):
        """Test ModelConfigResponse."""
        data = {
            "name": "gpt-4",
            "type": "api",
            "provider": "openai",
            "model_name": "gpt-4-turbo"
        }
        
        response = ModelConfigResponse(**data)
        assert response.name == "gpt-4"
        assert response.type == "api"
        assert response.provider == "openai"
        assert response.model_name == "gpt-4-turbo"
    
    def test_global_settings_response(self):
        """Test GlobalSettingsResponse."""
        data = {
            "temperature": 0.8,
            "max_tokens": 3000,
            "num_runs": 4,
            "vram_limit_percent": 75
        }
        
        response = GlobalSettingsResponse(**data)
        assert response.temperature == 0.8
        assert response.max_tokens == 3000
        assert response.num_runs == 4
        assert response.vram_limit_percent == 75
    
    def test_evaluation_config_response(self):
        """Test EvaluationConfigResponse."""
        data = {
            "auto_evaluate": True
        }
        
        response = EvaluationConfigResponse(**data)
        assert response.auto_evaluate is True
        
        # Test with False
        response_false = EvaluationConfigResponse(auto_evaluate=False)
        assert response_false.auto_evaluate is False
    
    def test_model_serialization(self):
        """Test model serialization to dict."""
        request = ModelConfigRequest(
            name="test-model",
            type="api",
            model_name="test",
            provider="test-provider"
        )
        
        data = request.model_dump()
        assert data["name"] == "test-model"
        assert data["type"] == "api"
        assert data["model_name"] == "test"
        assert data["provider"] == "test-provider"
        assert data["repo_id"] is None
    
    def test_model_json_serialization(self):
        """Test model JSON serialization."""
        settings = GlobalSettingsRequest(temperature=0.5, max_tokens=1000)
        
        json_str = settings.model_dump_json()
        assert '"temperature":0.5' in json_str or '"temperature": 0.5' in json_str
        assert '"max_tokens":1000' in json_str or '"max_tokens": 1000' in json_str
