"""Tests for configuration loader."""

import pytest
import tempfile
import yaml
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.config_loader import (
    ConfigLoader,
    ConfigurationError,
    ModelConfig,
    EvaluationConfig,
    PipelineConfig,
    StorageConfig,
    DashboardConfig,
    load_config,
    create_default_config
)


class TestModelConfig:
    """Test ModelConfig dataclass."""
    
    def test_valid_model_config(self):
        """Test creating valid model configuration."""
        config = ModelConfig(
            name="test-model",
            model_id="provider/test-model-v1",
            provider="anthropic",
            max_tokens=100000,
            enabled=True,
            notes="Test model"
        )
        assert config.name == "test-model"
        assert config.provider == "anthropic"
        assert config.enabled is True
    
    def test_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ConfigurationError, match="Unknown provider"):
            ModelConfig(
                name="test",
                model_id="test",
                provider="invalid_provider",
                max_tokens=1000
            )
    
    def test_invalid_max_tokens(self):
        """Test invalid max_tokens raises error."""
        with pytest.raises(ConfigurationError, match="Invalid max_tokens"):
            ModelConfig(
                name="test",
                model_id="test",
                provider="openai",
                max_tokens=-1
            )
    
    def test_missing_required_fields(self):
        """Test missing required fields raises error."""
        with pytest.raises(ConfigurationError):
            ModelConfig(
                name="",
                model_id="test",
                provider="openai",
                max_tokens=1000
            )


class TestEvaluationConfig:
    """Test EvaluationConfig dataclass."""
    
    def test_valid_evaluation_config(self):
        """Test creating valid evaluation configuration."""
        config = EvaluationConfig(
            evaluator_model="gemini-pro",
            evaluator_provider="google",
            temperature_generation=0.8,
            temperature_evaluation=0.2
        )
        assert config.evaluator_model == "gemini-pro"
        assert config.temperature_generation == 0.8
    
    def test_invalid_temperature(self):
        """Test invalid temperature raises error."""
        with pytest.raises(ConfigurationError, match="Invalid temperature"):
            EvaluationConfig(
                evaluator_model="test",
                evaluator_provider="google",
                temperature_generation=3.0  # Too high
            )


class TestConfigLoader:
    """Test ConfigLoader class."""
    
    @pytest.fixture
    def valid_config_dict(self):
        """Create a valid configuration dictionary."""
        return {
            'models': {
                'anthropic': [
                    {
                        'name': 'claude-opus',
                        'model_id': 'claude-3-opus-20240229',
                        'max_tokens': 200000,
                        'enabled': True
                    },
                    {
                        'name': 'claude-sonnet',
                        'model_id': 'claude-3-sonnet-20240229',
                        'max_tokens': 200000,
                        'enabled': False
                    }
                ],
                'openai': [
                    {
                        'name': 'gpt-4',
                        'model_id': 'gpt-4',
                        'max_tokens': 128000,
                        'enabled': True
                    }
                ]
            },
            'evaluation': {
                'evaluator_model': 'claude-3-opus-20240229',
                'evaluator_provider': 'anthropic',
                'temperature_generation': 1.0,
                'temperature_evaluation': 0.3
            },
            'pipeline': {
                'runs_per_sequence': 3,
                'checkpoint_interval': 10
            },
            'storage': {
                'responses_collection': 'test_responses'
            },
            'dashboard': {
                'port': 8502
            }
        }
    
    @pytest.fixture
    def config_file(self, valid_config_dict):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_config_dict, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_load_valid_config(self, config_file):
        """Test loading valid configuration file."""
        loader = ConfigLoader(config_file)
        loader.load()
        
        # Check models loaded
        assert 'anthropic' in loader.models
        assert len(loader.models['anthropic']) == 2
        assert len(loader.models['openai']) == 1
        
        # Check only enabled models
        enabled = loader.enabled_models
        assert len(enabled) == 2  # claude-opus and gpt-4
        
        # Check evaluation config
        assert loader.evaluation.evaluator_model == 'claude-3-opus-20240229'
        assert loader.evaluation.temperature_generation == 1.0
    
    def test_missing_config_file(self):
        """Test error when config file doesn't exist."""
        loader = ConfigLoader("nonexistent.yaml")
        with pytest.raises(ConfigurationError, match="not found"):
            loader.load()
    
    def test_invalid_yaml(self):
        """Test error with invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: :")
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                loader.load()
        finally:
            Path(temp_path).unlink()
    
    def test_missing_required_sections(self):
        """Test error when required sections are missing."""
        config = {'models': {}}  # Missing evaluation section
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Missing 'evaluation'"):
                loader.load()
        finally:
            Path(temp_path).unlink()
    
    def test_get_model(self, config_file):
        """Test getting specific model configuration."""
        loader = ConfigLoader(config_file).load()
        
        # Get by name
        model = loader.get_model('anthropic', 'claude-opus')
        assert model is not None
        assert model.model_id == 'claude-3-opus-20240229'
        
        # Get by model_id
        model = loader.get_model('openai', 'gpt-4')
        assert model is not None
        assert model.name == 'gpt-4'
        
        # Non-existent model
        model = loader.get_model('anthropic', 'nonexistent')
        assert model is None
    
    def test_validate_warnings(self, config_file):
        """Test configuration validation warnings."""
        loader = ConfigLoader(config_file).load()
        warnings = loader.validate()
        
        # Should have no warnings for valid config
        assert len(warnings) == 0
        
        # Disable all models and check warning
        for models in loader.models.values():
            for model in models:
                model.enabled = False
        
        warnings = loader.validate()
        assert any("No enabled models" in w for w in warnings)
    
    def test_to_dict_and_save(self, config_file):
        """Test converting to dict and saving."""
        loader = ConfigLoader(config_file).load()
        
        # Convert to dict
        config_dict = loader.to_dict()
        assert 'models' in config_dict
        assert 'evaluation' in config_dict
        
        # Save to new file
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            loader.save(temp_path)
            
            # Load saved file and verify
            new_loader = ConfigLoader(temp_path).load()
            assert len(new_loader.enabled_models) == len(loader.enabled_models)
        finally:
            Path(temp_path).unlink()
    
    def test_all_models_property(self, config_file):
        """Test getting all models as flat list."""
        loader = ConfigLoader(config_file).load()
        all_models = loader.all_models
        
        assert len(all_models) == 3  # 2 anthropic + 1 openai
        assert all(isinstance(m, ModelConfig) for m in all_models)
    
    def test_optional_sections_defaults(self):
        """Test optional sections get default values."""
        config = {
            'models': {'anthropic': [{'name': 'test', 'model_id': 'test', 'max_tokens': 1000}]},
            'evaluation': {'evaluator_model': 'test', 'evaluator_provider': 'anthropic'}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path).load()
            
            # Check defaults are applied
            assert loader.pipeline.runs_per_sequence == 3
            assert loader.storage.responses_collection == "responses"
            assert loader.dashboard.port == 8501
        finally:
            Path(temp_path).unlink()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def temp_config(self):
        """Create a minimal temp config for testing."""
        config_data = {
            "models": [
                {
                    "name": "test-model", 
                    "provider": "openai", 
                    "api_base": "test", 
                    "max_tokens": 100,
                    "enabled": True
                }
            ],
            "evaluations": {"temperature": 0.7, "max_tokens": 100},
            "pipeline": {"enabled": True},
            "storage": {"enabled": True},
            "dashboard": {"enabled": True}
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            yield f.name
        Path(f.name).unlink()
    
    def test_load_config_function(self, temp_config):
        """Test load_config convenience function."""
        loader = load_config(temp_config)
        assert isinstance(loader, ConfigLoader)
        assert len(loader.enabled_models) > 0
    
    def test_create_default_config(self):
        """Test creating default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            create_default_config(config_path)
            
            assert config_path.exists()
            
            # Load created config
            loader = ConfigLoader(config_path).load()
            assert len(loader.models) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
