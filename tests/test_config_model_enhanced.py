"""Enhanced config model tests for coverage boost."""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.models.config import Config, GlobalSettings, ModelConfig, EvaluationConfig


class TestConfigModelEnhanced:
    """Enhanced config model tests."""
    
    def test_config_load_from_file(self):
        """Test loading config from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
version: 1
global_settings:
  output_dir: "test_output"
  log_level: "INFO"
models:
  - name: "test-model"
    provider: "openai"
    model_name: "gpt-3.5-turbo"
    api_base: "https://api.openai.com/v1"
    max_tokens: 2048
    enabled: true
prompts:
  - name: "test-prompt"
    content: "Test prompt content"
    system_prompt: "You are helpful"
evaluation:
  temperature: 0.7
  max_tokens: 1000
"""
            f.write(config_content)
            temp_path = f.name
            
        try:
            config = Config.load_config(temp_path)
            
            assert config.version == 1
            assert config.global_settings.output_dir == "test_output"
            assert len(config.models) == 1
            assert config.models[0].name == "test-model"
            assert len(config.prompts) == 1
            assert config.prompts[0].name == "test-prompt"
            
        finally:
            Path(temp_path).unlink()
            
    def test_config_save_to_file(self):
        """Test saving config to file."""
        config = Config()
        config.version = 2
        config.global_settings = GlobalSettings(output_dir="custom_output")
        
        model = ModelConfig(
            name="save-test-model",
            provider="anthropic", 
            model_name="claude-3",
            api_base="https://api.anthropic.com",
            max_tokens=4096,
            enabled=True
        )
        config.models = [model]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
            
        try:
            config.save_config(temp_path)
            
            # Load it back to verify
            loaded_config = Config.load_config(temp_path)
            assert loaded_config.version == 2
            assert loaded_config.global_settings.output_dir == "custom_output"
            assert len(loaded_config.models) == 1
            assert loaded_config.models[0].name == "save-test-model"
            
        finally:
            Path(temp_path).unlink()
            
    def test_config_get_model_by_name(self):
        """Test getting model by name."""
        config = Config()
        model1 = ModelConfig(
            name="model1", provider="openai", model_name="gpt-4",
            api_base="test", max_tokens=1000, enabled=True
        )
        model2 = ModelConfig(
            name="model2", provider="anthropic", model_name="claude-3",
            api_base="test", max_tokens=2000, enabled=False
        )
        config.models = [model1, model2]
        
        found_model = config.get_model_by_name("model1")
        assert found_model == model1
        
        not_found = config.get_model_by_name("nonexistent")
        assert not_found is None
        
    def test_config_get_enabled_models(self):
        """Test getting only enabled models."""
        config = Config()
        model1 = ModelConfig(
            name="enabled", provider="openai", model_name="gpt-4",
            api_base="test", max_tokens=1000, enabled=True
        )
        model2 = ModelConfig(
            name="disabled", provider="anthropic", model_name="claude-3", 
            api_base="test", max_tokens=2000, enabled=False
        )
        config.models = [model1, model2]
        
        enabled_models = config.get_enabled_models()
        
        assert len(enabled_models) == 1
        assert enabled_models[0].name == "enabled"
        
    def test_config_add_model(self):
        """Test adding model to config."""
        config = Config()
        model = ModelConfig(
            name="new-model", provider="openai", model_name="gpt-4",
            api_base="test", max_tokens=1000, enabled=True
        )
        
        config.add_model(model)
        
        assert len(config.models) == 1
        assert config.models[0] == model
        
    def test_config_remove_model(self):
        """Test removing model from config."""
        config = Config()
        model1 = ModelConfig(
            name="keep", provider="openai", model_name="gpt-4",
            api_base="test", max_tokens=1000, enabled=True
        )
        model2 = ModelConfig(
            name="remove", provider="anthropic", model_name="claude-3",
            api_base="test", max_tokens=2000, enabled=True
        )
        config.models = [model1, model2]
        
        config.remove_model("remove")
        
        assert len(config.models) == 1
        assert config.models[0].name == "keep"
        
    def test_config_validation_methods(self):
        """Test config validation methods."""
        config = Config()
        
        # Test with valid config
        config.global_settings = GlobalSettings()
        model = ModelConfig(
            name="valid", provider="openai", model_name="gpt-4",
            api_base="https://api.openai.com/v1", max_tokens=1000, enabled=True
        )
        config.models = [model]
        
        assert config.is_valid()
        
        # Test validation with invalid model
        invalid_model = ModelConfig(
            name="", provider="openai", model_name="gpt-4",  # Empty name
            api_base="test", max_tokens=1000, enabled=True
        )
        config.models = [invalid_model]
        
        assert not config.is_valid()
        
    def test_global_settings_defaults(self):
        """Test GlobalSettings default values."""
        settings = GlobalSettings()
        
        assert settings.output_dir == "output"
        assert settings.log_level == "INFO"
        assert settings.max_concurrent_requests == 5
        assert settings.request_timeout == 30.0
        
    def test_global_settings_custom_values(self):
        """Test GlobalSettings with custom values."""
        settings = GlobalSettings(
            output_dir="custom_output",
            log_level="DEBUG", 
            max_concurrent_requests=10,
            request_timeout=60.0
        )
        
        assert settings.output_dir == "custom_output"
        assert settings.log_level == "DEBUG"
        assert settings.max_concurrent_requests == 10
        assert settings.request_timeout == 60.0
        
    def test_evaluation_config_defaults(self):
        """Test EvaluationConfig default values."""
        eval_config = EvaluationConfig()
        
        assert eval_config.temperature == 0.7
        assert eval_config.max_tokens == 2048
        assert eval_config.top_p == 1.0
        assert eval_config.frequency_penalty == 0.0
        assert eval_config.presence_penalty == 0.0
