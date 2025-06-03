"""
Comprehensive tests for models/config.py
These tests cover Configuration management, model definitions, and validation.
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List

# Import the models we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.models.config import (
    GlobalSettings,
    ModelConfig,
    EvaluationConfig,
    Config
)


class TestGlobalSettings:
    """Test the GlobalSettings dataclass."""
    
    def test_default_global_settings(self):
        """Test creating GlobalSettings with default values."""
        settings = GlobalSettings()
        
        assert settings.temperature == 0.9
        assert settings.max_tokens == 4096
        assert settings.num_runs == 3
        assert settings.vram_limit_percent == 80
    
    def test_custom_global_settings(self):
        """Test creating GlobalSettings with custom values."""
        settings = GlobalSettings(
            temperature=0.7,
            max_tokens=2048,
            num_runs=5,
            vram_limit_percent=70
        )
        
        assert settings.temperature == 0.7
        assert settings.max_tokens == 2048
        assert settings.num_runs == 5
        assert settings.vram_limit_percent == 70


class TestModelConfig:
    """Test the ModelConfig dataclass."""
    
    def test_required_model_config_fields(self):
        """Test creating ModelConfig with required fields."""
        config = ModelConfig(
            name="gpt-4",
            type="api",            provider="openai",
            model_name="gpt-4"
        )
        
        assert config.name == "gpt-4"
        assert config.type == "api"
        assert config.provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.repo_id is None
        assert config.filename is None
        assert config.subdirectory is None
        assert config.model_settings is None


class TestEvaluationConfig:
    """Test the EvaluationConfig dataclass."""
    
    def test_default_evaluation_config(self):
        """Test creating EvaluationConfig with default values."""
        config = EvaluationConfig()
        
        assert config.auto_evaluate == True
        assert config.max_retries == 5
        assert config.evaluator_models == ["claude-3-sonnet", "gemini-pro"]
    
    def test_post_init_sets_default_evaluator_models(self):
        """Test that __post_init__ sets default evaluator models when None."""
        config = EvaluationConfig(evaluator_models=None)
        assert config.evaluator_models == ["claude-3-sonnet", "gemini-pro"]


class TestConfig:
    """Test the main Config class."""
    
    def test_config_initialization(self):
        """Test Config class initialization."""
        config_path = "/tmp/test_config.yaml"
        config = Config(config_path)
        
        assert config.config_path == Path(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
