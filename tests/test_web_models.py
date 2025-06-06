"""
Comprehensive tests for web/models/requests.py and responses.py
These tests cover API request/response models and validation.
"""

import pytest
from typing import Dict, Any

# Import the models we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.web.models.requests import (
    ModelConfigRequest,
    GlobalSettingsRequest,
    EvaluationConfigRequest
)

from storybench.web.models.responses import (
    ModelConfigResponse,
    GlobalSettingsResponse,
    EvaluationConfigResponse
)


class TestModelConfigRequest:
    """Test the ModelConfigRequest model."""
    
    def test_api_model_config_request(self):
        """Test creating API model configuration request."""
        request = ModelConfigRequest(
            name="gpt-4",
            type="api",
            provider="openai",
            model_name="gpt-4"
        )
        
        assert request.name == "gpt-4"
        assert request.type == "api"
        assert request.provider == "openai"
        assert request.model_name == "gpt-4"
        assert request.repo_id is None
        assert request.filename is None
        assert request.subdirectory is None
    
    def test_local_model_config_request(self):
        """Test creating local model configuration request."""
        request = ModelConfigRequest(
            name="llama-7b",
            type="local",
            model_name="llama-7b-chat",
            repo_id="meta-llama/Llama-2-7b-chat-hf",
            filename="pytorch_model.bin",
            subdirectory="models"
        )
        
        assert request.name == "llama-7b"
        assert request.type == "local"
        assert request.model_name == "llama-7b-chat"
        assert request.repo_id == "meta-llama/Llama-2-7b-chat-hf"
        assert request.filename == "pytorch_model.bin"
        assert request.subdirectory == "models"
    
    def test_invalid_model_type_raises_error(self):
        """Test that invalid model type raises validation error."""
        with pytest.raises(ValueError):
            ModelConfigRequest(
                name="test",
                type="invalid_type",  # Should be "api" or "local"
                model_name="test"
            )


class TestGlobalSettingsRequest:
    """Test the GlobalSettingsRequest model."""
    
    def test_default_global_settings_request(self):
        """Test creating GlobalSettingsRequest with defaults."""
        request = GlobalSettingsRequest()
        
        assert request.temperature == 0.9
        assert request.max_tokens == 4096
        assert request.num_runs == 3
        assert request.vram_limit_percent == 80
    
    def test_custom_global_settings_request(self):
        """Test creating GlobalSettingsRequest with custom values."""
        request = GlobalSettingsRequest(
            temperature=0.7,
            max_tokens=2048,
            num_runs=5,
            vram_limit_percent=70
        )
        
        assert request.temperature == 0.7
        assert request.max_tokens == 2048
        assert request.num_runs == 5
        assert request.vram_limit_percent == 70
    
    def test_temperature_validation(self):
        """Test temperature field validation."""
        with pytest.raises(ValueError):
            GlobalSettingsRequest(temperature=3.0)  # > 2.0
        
        with pytest.raises(ValueError):
            GlobalSettingsRequest(temperature=-0.1)  # < 0.0
    
    def test_max_tokens_validation(self):
        """Test max_tokens field validation."""
        with pytest.raises(ValueError):
            GlobalSettingsRequest(max_tokens=0)  # < 1
        
        with pytest.raises(ValueError):
            GlobalSettingsRequest(max_tokens=50000)  # > 32000
    
    def test_num_runs_validation(self):
        """Test num_runs field validation."""
        with pytest.raises(ValueError):
            GlobalSettingsRequest(num_runs=0)  # < 1
        
        with pytest.raises(ValueError):
            GlobalSettingsRequest(num_runs=15)  # > 10


class TestModelConfigResponse:
    """Test the ModelConfigResponse model."""
    
    def test_model_config_response_creation(self):
        """Test creating ModelConfigResponse."""
        response = ModelConfigResponse(
            name="gpt-4",
            type="api",
            provider="openai",
            model_name="gpt-4"
        )
        
        assert response.name == "gpt-4"
        assert response.type == "api"
        assert response.provider == "openai"
        assert response.model_name == "gpt-4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
