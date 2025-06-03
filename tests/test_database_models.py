"""Test Pydantic models for MongoDB documents."""

import pytest
from datetime import datetime
from bson import ObjectId

from src.storybench.database.models import (
    Evaluation, 
    EvaluationStatus, 
    GlobalSettings,
    ModelConfig,
    ModelType
)

class TestPydanticModels:
    """Test Pydantic model validation and serialization."""
    
    def test_evaluation_model_creation(self):
        """Test creating an Evaluation model."""
        global_settings = GlobalSettings(
            temperature=0.7,
            max_tokens=2000,
            num_runs=3
        )
        
        evaluation = Evaluation(
            config_hash="test_hash_123",
            models=["gpt-4", "claude-3"],
            global_settings=global_settings,
            total_tasks=100
        )
        
        assert evaluation.config_hash == "test_hash_123"
        assert evaluation.status == EvaluationStatus.IN_PROGRESS
        assert evaluation.total_tasks == 100
        assert evaluation.completed_tasks == 0
        
    def test_model_config_creation(self):
        """Test creating a ModelConfig."""
        model_config = ModelConfig(
            name="gpt-4",
            type=ModelType.API,
            provider="openai",
            model_name="gpt-4"
        )
        
        assert model_config.name == "gpt-4"
        assert model_config.type == ModelType.API
        assert model_config.provider == "openai"
