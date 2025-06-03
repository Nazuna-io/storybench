"""Test additional config functionality."""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.storybench.models.config import Config, GlobalSettings, ModelConfig, EvaluationConfig


class TestConfigAdvanced:
    """Test advanced Config functionality."""
    
    def test_get_version_hash_consistency(self):
        """Test that version hash is consistent for same configuration."""
        # Create sample config
        global_settings = GlobalSettings(temperature=0.7, max_tokens=2000, num_runs=3)
        evaluation = EvaluationConfig()
        
        config1 = Config()
        config1.global_settings = global_settings
        config1.evaluation = evaluation
        config1.prompts = {"seq1": ["prompt1", "prompt2"]}
        
        config2 = Config()
        config2.global_settings = global_settings
        config2.evaluation = evaluation
        config2.prompts = {"seq1": ["prompt1", "prompt2"]}
        
        hash1 = config1.get_version_hash()
        hash2 = config2.get_version_hash()
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    def test_get_version_hash_different_configs(self):
        """Test that different configurations produce different hashes."""
        global_settings1 = GlobalSettings(temperature=0.7, max_tokens=2000, num_runs=3)
        global_settings2 = GlobalSettings(temperature=0.8, max_tokens=2000, num_runs=3)
        
        config1 = Config()
        config1.global_settings = global_settings1
        config1.prompts = {"seq1": ["prompt1"]}
        
        config2 = Config()
        config2.global_settings = global_settings2
        config2.prompts = {"seq1": ["prompt1"]}
        
        hash1 = config1.get_version_hash()
        hash2 = config2.get_version_hash()
        
        assert hash1 != hash2
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = Config()
        config.global_settings = GlobalSettings()
        config.evaluation = EvaluationConfig()
        config.models = [
            ModelConfig(name="test", type="api", provider="openai", model_name="gpt-4")
        ]
        config.prompts = {"seq1": ["prompt1"]}
        config.evaluation_criteria = {"creativity": {"description": "Test creativity"}}
        
        errors = config.validate()
        assert errors == []
    
    def test_validate_no_models(self):
        """Test validation with no models."""
        config = Config()
        config.global_settings = GlobalSettings()
        config.evaluation = EvaluationConfig()
        config.models = []
        config.prompts = {"seq1": ["prompt1"]}
        config.evaluation_criteria = {"creativity": {"description": "Test"}}
        
        errors = config.validate()
        assert "No models configured" in errors
    
    def test_validate_no_prompts(self):
        """Test validation with no prompts."""
        config = Config()
        config.global_settings = GlobalSettings()
        config.evaluation = EvaluationConfig()
        config.models = [ModelConfig(name="test", type="api", provider="openai", model_name="gpt-4")]
        config.prompts = {}
        config.evaluation_criteria = {"creativity": {"description": "Test"}}
        
        errors = config.validate()
        assert "No prompt sequences configured" in errors
    
    def test_validate_empty_prompt_sequence(self):
        """Test validation with empty prompt sequence."""
        config = Config()
        config.global_settings = GlobalSettings()
        config.evaluation = EvaluationConfig()
        config.models = [ModelConfig(name="test", type="api", provider="openai", model_name="gpt-4")]
        config.prompts = {"seq1": []}
        config.evaluation_criteria = {"creativity": {"description": "Test"}}
        
        errors = config.validate()
        assert "Prompt sequence 'seq1' is empty" in errors
    
    def test_validate_no_evaluation_criteria(self):
        """Test validation with no evaluation criteria."""
        config = Config()
        config.global_settings = GlobalSettings()
        config.evaluation = EvaluationConfig()
        config.models = [ModelConfig(name="test", type="api", provider="openai", model_name="gpt-4")]
        config.prompts = {"seq1": ["prompt1"]}
        config.evaluation_criteria = {}
        
        errors = config.validate()
        assert "No evaluation criteria configured" in errors
    
    def test_validate_multiple_errors(self):
        """Test validation with multiple errors."""
        config = Config()
        config.global_settings = GlobalSettings()
        config.evaluation = EvaluationConfig()
        config.models = []  # No models
        config.prompts = {}  # No prompts
        config.evaluation_criteria = {}  # No criteria
        
        errors = config.validate()
        assert len(errors) >= 3
        assert any("No models configured" in error for error in errors)
        assert any("No prompt sequences configured" in error for error in errors)
        assert any("No evaluation criteria configured" in error for error in errors)
