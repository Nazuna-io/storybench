"""Comprehensive tests for web models."""

import pytest
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly without going through __init__ to avoid web dependencies
from storybench.web.models.requests import (
    ModelConfigRequest,
    PromptRequest,
    EvaluationRequest,
    BatchEvaluationRequest,
    ValidationRequest,
    CriteriaRequest
)
from storybench.web.models.responses import (
    ModelResponse,
    PromptResponse,
    EvaluationResponse,
    ResponseAnalysis,
    ValidationResult,
    ErrorResponse,
    SuccessResponse,
    BatchEvaluationResponse,
    CriteriaResponse
)


class TestWebRequestModels:
    """Test web request models."""
    
    def test_model_config_request_api_model(self):
        """Test ModelConfigRequest for API models."""
        request = ModelConfigRequest(
            name="test-api-model",
            type="api",
            provider="openai",
            model_name="gpt-3.5-turbo"
        )
        
        assert request.name == "test-api-model"
        assert request.type == "api"
        assert request.provider == "openai"
        assert request.model_name == "gpt-3.5-turbo"
        assert request.repo_id is None
        assert request.filename is None
        
    def test_model_config_request_local_model(self):
        """Test ModelConfigRequest for local models."""
        request = ModelConfigRequest(
            name="test-local-model",
            type="local",
            model_name="llama2-7b",
            repo_id="meta-llama/Llama-2-7b-hf",
            filename="pytorch_model.bin",
            subdirectory="models"
        )
        
        assert request.name == "test-local-model"
        assert request.type == "local"
        assert request.model_name == "llama2-7b"
        assert request.repo_id == "meta-llama/Llama-2-7b-hf"
        assert request.filename == "pytorch_model.bin"
        assert request.subdirectory == "models"
        
    def test_prompt_request_basic(self):
        """Test basic PromptRequest."""
        request = PromptRequest(
            name="test-prompt",
            content="Tell me about {topic}",
            system_prompt="You are a helpful assistant"
        )
        
        assert request.name == "test-prompt"
        assert request.content == "Tell me about {topic}"
        assert request.system_prompt == "You are a helpful assistant"
        
    def test_evaluation_request_basic(self):
        """Test basic EvaluationRequest."""
        request = EvaluationRequest(
            model_name="test-model",
            prompt_name="test-prompt"
        )
        
        assert request.model_name == "test-model"
        assert request.prompt_name == "test-prompt"
        assert request.variables == {}
        assert request.expected_output is None
        
    def test_evaluation_request_with_variables(self):
        """Test EvaluationRequest with variables."""
        request = EvaluationRequest(
            model_name="test-model",
            prompt_name="test-prompt",
            variables={"topic": "artificial intelligence"},
            expected_output="AI is a field of computer science"
        )
        
        assert request.variables == {"topic": "artificial intelligence"}
        assert request.expected_output == "AI is a field of computer science"
        
    def test_batch_evaluation_request(self):
        """Test BatchEvaluationRequest."""
        request = BatchEvaluationRequest(
            model_names=["model1", "model2"],
            prompt_names=["prompt1", "prompt2"],
            variables={"topic": "test"}
        )
        
        assert request.model_names == ["model1", "model2"]
        assert request.prompt_names == ["prompt1", "prompt2"]
        assert request.variables == {"topic": "test"}
        
    def test_validation_request(self):
        """Test ValidationRequest."""
        request = ValidationRequest(
            model_name="test-model",
            prompt_content="Test prompt"
        )
        
        assert request.model_name == "test-model"
        assert request.prompt_content == "Test prompt"
        
    def test_criteria_request(self):
        """Test CriteriaRequest."""
        request = CriteriaRequest(
            name="test-criteria",
            description="Test description",
            weight=0.8
        )
        
        assert request.name == "test-criteria"
        assert request.description == "Test description" 
        assert request.weight == 0.8


class TestWebResponseModels:
    """Test web response models."""
    
    def test_model_response(self):
        """Test ModelResponse."""
        response = ModelResponse(
            id=1,
            name="test-model",
            type="api",
            provider="openai",
            model_name="gpt-3.5-turbo",
            enabled=True
        )
        
        assert response.id == 1
        assert response.name == "test-model"
        assert response.enabled is True
    
    def test_prompt_response(self):
        """Test PromptResponse."""
        response = PromptResponse(
            id=1,
            name="test-prompt",
            content="Test content",
            system_prompt="System prompt"
        )
        
        assert response.id == 1
        assert response.name == "test-prompt"
        
    def test_evaluation_response(self):
        """Test EvaluationResponse."""
        response = EvaluationResponse(
            id=1,
            model_name="test-model",
            prompt_name="test-prompt",
            status="completed",
            response_text="Test response",
            tokens_used=100,
            response_time=1.5
        )
        
        assert response.id == 1
        assert response.status == "completed"
        assert response.tokens_used == 100
        assert response.response_time == 1.5
        
    def test_success_response(self):
        """Test SuccessResponse."""
        response = SuccessResponse(
            message="Operation successful",
            data={"key": "value"}
        )
        
        assert response.success is True
        assert response.message == "Operation successful"
        assert response.data == {"key": "value"}
        
    def test_error_response(self):
        """Test ErrorResponse."""
        response = ErrorResponse(
            message="Error occurred",
            details="Detailed error info"
        )
        
        assert response.success is False
        assert response.message == "Error occurred"
        assert response.details == "Detailed error info"
        
    def test_validation_result(self):
        """Test ValidationResult."""
        result = ValidationResult(
            is_valid=True,
            estimated_tokens=150,
            warnings=["Warning message"]
        )
        
        assert result.is_valid is True
        assert result.estimated_tokens == 150
        assert result.warnings == ["Warning message"]
