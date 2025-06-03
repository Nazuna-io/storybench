"""
Comprehensive tests for database models.
These tests cover Pydantic model validation, serialization, and business logic.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from bson import ObjectId

# Import the models we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.database.models import (
    PyObjectId,
    EvaluationStatus,
    ModelType,
    ResponseStatus,
    GlobalSettings,
    ModelConfigItem,
    EvaluationRunConfig,
    PromptItemConfig,
    EvaluationCriterionItem,
    CriterionEvaluation,
    Evaluation,
    Response,
    EvaluationScore,
    ResponseLLMEvaluation,
    ApiKeys
)


class TestPyObjectId:
    """Test the custom PyObjectId type."""
    
    def test_valid_object_id_creation(self):
        """Test creating PyObjectId from valid ObjectId."""
        original_id = ObjectId()
        py_id = PyObjectId(original_id)
        assert py_id == original_id
        assert isinstance(py_id, ObjectId)
    
    def test_valid_string_creation(self):
        """Test creating PyObjectId from valid string."""
        id_str = "507f1f77bcf86cd799439011"
        py_id = PyObjectId(id_str)
        assert str(py_id) == id_str
        assert isinstance(py_id, ObjectId)
    
    def test_invalid_string_raises_error(self):
        """Test that invalid string raises InvalidId."""
        from bson.errors import InvalidId
        with pytest.raises(InvalidId):
            PyObjectId("invalid_id")
    
    def test_serialization_to_string(self):
        """Test that PyObjectId serializes to string in JSON."""
        original_id = ObjectId()
        py_id = PyObjectId(original_id)
        assert str(py_id) == str(original_id)


class TestEvaluationStatus:
    """Test the EvaluationStatus enum."""
    
    def test_enum_values(self):
        """Test that enum has expected values."""
        assert EvaluationStatus.IN_PROGRESS == "in_progress"
    
    def test_enum_comparison(self):
        """Test enum comparison."""
        status1 = EvaluationStatus.IN_PROGRESS
        status2 = EvaluationStatus.IN_PROGRESS
        assert status1 == status2


class TestModelConfigItem:
    """Test the ModelConfigItem model."""
    
    def test_valid_model_config_creation(self):
        """Test creating a valid model configuration."""
        config = ModelConfigItem(
            name="gpt-4",
            type="api",
            provider="openai",
            model_name="gpt-4"
        )
        
        assert config.name == "gpt-4"
        assert config.type == "api"
        assert config.provider == "openai"
        assert config.model_name == "gpt-4"


class TestGlobalSettings:
    """Test the GlobalSettings model."""
    
    def test_valid_global_settings(self):
        """Test creating valid global settings."""
        settings = GlobalSettings(
            temperature=0.7,
            max_tokens=1000,
            num_runs=5,
            vram_limit_percent=80.0
        )
        
        assert settings.temperature == 0.7
        assert settings.max_tokens == 1000
        assert settings.num_runs == 5
        assert settings.vram_limit_percent == 80.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestPromptItemConfig:
    """Test the PromptItemConfig model."""
    
    def test_valid_prompt_item_config(self):
        """Test creating a valid prompt item configuration."""
        prompt = PromptItemConfig(
            name="test_prompt",
            text="This is a test prompt: {variable}",
            variables=["variable"]
        )
        
        assert prompt.name == "test_prompt"
        assert prompt.text == "This is a test prompt: {variable}"
        assert prompt.variables == ["variable"]


class TestEvaluationCriterionItem:
    """Test the EvaluationCriterionItem model."""
    
    def test_valid_criterion_item(self):
        """Test creating a valid criterion item."""
        criterion = EvaluationCriterionItem(
            name="coherence",
            description="Measures logical flow",
            weight=0.5,
            prompt_template="Rate coherence: {content}"
        )
        
        assert criterion.name == "coherence"
        assert criterion.description == "Measures logical flow"
        assert criterion.weight == 0.5
        assert criterion.prompt_template == "Rate coherence: {content}"


class TestResponse:
    """Test the Response model."""
    
    def test_valid_response_creation(self):
        """Test creating a valid response."""
        response = Response(
            model_name="gpt-4",
            prompt_name="test_prompt",
            response_text="This is a test response",
            timestamp=datetime.now(timezone.utc)
        )
        
        assert response.model_name == "gpt-4"
        assert response.prompt_name == "test_prompt"
        assert response.response_text == "This is a test response"
        assert response.timestamp is not None


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_model_to_dict_conversion(self):
        """Test that models can be serialized to dictionaries."""
        config = ModelConfigItem(
            name="test-model",
            type="api",
            provider="openai", 
            model_name="gpt-4"
        )
        
        config_dict = config.model_dump()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "test-model"
        assert config_dict["type"] == "api"
        
        # Test that we can recreate from dict
        recreated = ModelConfigItem(**config_dict)
        assert recreated.name == config.name
        assert recreated.type == config.type
