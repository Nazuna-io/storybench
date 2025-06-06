"""Isolated tests for web models that bypass init imports."""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add direct path to avoid __init__ imports  
models_path = str(Path(__file__).parent.parent / "src" / "storybench" / "web" / "models")
sys.path.insert(0, models_path)

# Import modules directly
import requests
import responses


class TestWebModelsIsolated:
    """Test web models in isolation."""
    
    def test_model_config_request_creation(self):
        """Test ModelConfigRequest creation."""
        request = requests.ModelConfigRequest(
            name="test-model",
            type="api", 
            model_name="gpt-3.5-turbo"
        )
        
        assert request.name == "test-model"
        assert request.type == "api"
        assert request.model_name == "gpt-3.5-turbo"
        
    def test_prompt_request_creation(self):
        """Test PromptRequest creation."""
        request = requests.PromptRequest(
            name="test-prompt",
            content="Test content"
        )
        
        assert request.name == "test-prompt"
        assert request.content == "Test content"
        
    def test_evaluation_request_creation(self):
        """Test EvaluationRequest creation."""
        request = requests.EvaluationRequest(
            model_name="test-model",
            prompt_name="test-prompt"
        )
        
        assert request.model_name == "test-model"
        assert request.prompt_name == "test-prompt"
        
    def test_model_response_creation(self):
        """Test ModelResponse creation."""
        response = responses.ModelResponse(
            id=1,
            name="test-model",
            type="api",
            model_name="gpt-3.5-turbo",
            enabled=True
        )
        
        assert response.id == 1
        assert response.name == "test-model"
        assert response.enabled is True
        
    def test_success_response_creation(self):
        """Test SuccessResponse creation."""
        response = responses.SuccessResponse(
            message="Success"
        )
        
        assert response.success is True
        assert response.message == "Success"
