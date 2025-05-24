"""Test CLI functionality."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.cli import cli, _get_api_keys, _check_required_api_keys
from storybench.models.config import ModelConfig


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock configuration file."""
    # Create the main config file
    config_path = Path(temp_dir) / "test_config.yaml"
    config_path.write_text("")  # Empty main config
    
    # Create models.yaml file that the loader expects
    models_data = {
        'version': 1,
        'global_settings': {
            'temperature': 0.9,
            'max_tokens': 4096,
            'num_runs': 2,
            'vram_limit_percent': 80
        },
        'models': [
            {
                'name': 'TestOpenAI',
                'type': 'api',
                'provider': 'openai',
                'model_name': 'gpt-4'
            }
        ],
        'evaluation': {}
    }
    
    models_path = Path(temp_dir) / "models.yaml"
    import yaml
    with open(models_path, 'w') as f:
        yaml.dump(models_data, f)
    
    # Create prompts.json file
    prompts_data = {
        'TestSequence': [
            {'name': 'Prompt1', 'text': 'Test prompt 1'}
        ]
    }
    
    prompts_path = Path(temp_dir) / "prompts.json"
    import json
    with open(prompts_path, 'w') as f:
        json.dump(prompts_data, f)
    
    # Create evaluation_criteria.yaml
    criteria_data = {
        'version': 1,
        'criteria': {
            'creativity': {
                'name': 'Creativity',
                'description': 'Test criteria',
                'scale': 5
            }
        }
    }
    
    criteria_path = Path(temp_dir) / "evaluation_criteria.yaml"
    with open(criteria_path, 'w') as f:
        yaml.dump(criteria_data, f)
    
    return str(config_path)


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    env_vars = {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key'
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


class TestCLICommands:
    """Test CLI command functionality."""
    
    def test_cli_group_exists(self):
        """Test that CLI group is properly defined."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "StorybenchLLM" in result.output
        assert "evaluate" in result.output
        assert "validate" in result.output
        assert "clean" in result.output
    
    def test_validate_command_with_valid_config(self, mock_config_file):
        """Test validate command with valid configuration."""
        runner = CliRunner()
        result = runner.invoke(cli, ['validate', '--config', mock_config_file])
        assert result.exit_code == 0
        assert "Configuration is valid" in result.output
    
    def test_validate_command_with_missing_config(self):
        """Test validate command with missing configuration file."""
        runner = CliRunner()
        result = runner.invoke(cli, ['validate', '--config', 'nonexistent.yaml'])
        assert result.exit_code == 0
        assert "Error loading configuration" in result.output    
    def test_clean_command_with_models_dir(self, temp_dir):
        """Test clean command with models directory."""
        # Create models directory with test files
        models_dir = Path(temp_dir) / "models"
        models_dir.mkdir()
        
        test_model = models_dir / "test.gguf"
        test_model.write_text("fake model data")
        
        # Change to temp directory so clean command finds our models dir
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            runner = CliRunner()
            result = runner.invoke(cli, ['clean', '--models'])
            assert result.exit_code == 0
            assert "Removed" in result.output
            assert "Local models cleaned" in result.output
            assert not test_model.exists()
        finally:
            os.chdir(original_cwd)


class TestAPIKeyFunctions:
    """Test API key related functions."""
    
    def test_get_api_keys(self, mock_env):
        """Test _get_api_keys function."""
        api_keys = _get_api_keys()
        assert api_keys['OPENAI_API_KEY'] == 'test-openai-key'
        assert api_keys['ANTHROPIC_API_KEY'] == 'test-anthropic-key'
        assert 'GOOGLE_API_KEY' in api_keys
        assert 'QWEN_API_KEY' in api_keys
        assert 'AI21_API_KEY' in api_keys
    
    def test_check_required_api_keys_missing(self):
        """Test _check_required_api_keys with missing keys."""
        models = [
            ModelConfig(
                name="TestOpenAI",
                type="api",
                provider="openai",
                model_name="gpt-4"
            ),
            ModelConfig(
                name="TestAnthropic",
                type="api", 
                provider="anthropic",
                model_name="claude-3"
            )
        ]        
        api_keys = {
            'OPENAI_API_KEY': 'test-key',
            'ANTHROPIC_API_KEY': None,  # Missing
            'GOOGLE_API_KEY': None,
            'QWEN_API_KEY': None,
            'AI21_API_KEY': None
        }
        
        missing = _check_required_api_keys(models, api_keys)
        assert 'ANTHROPIC_API_KEY' in missing
        assert 'OPENAI_API_KEY' not in missing
    
    def test_check_required_api_keys_all_present(self):
        """Test _check_required_api_keys with all keys present."""
        models = [
            ModelConfig(
                name="TestOpenAI",
                type="api",
                provider="openai", 
                model_name="gpt-4"
            )
        ]
        
        api_keys = {
            'OPENAI_API_KEY': 'test-key',
            'ANTHROPIC_API_KEY': 'test-key',
            'GOOGLE_API_KEY': 'test-key',
            'QWEN_API_KEY': 'test-key',
            'AI21_API_KEY': 'test-key'
        }
        
        missing = _check_required_api_keys(models, api_keys)
        assert len(missing) == 0
    
    def test_check_required_api_keys_local_models(self):
        """Test _check_required_api_keys with local models (should not require API keys)."""
        models = [
            ModelConfig(
                name="TestLocal",
                type="local",
                provider="local",
                model_name="test.gguf",
                filename="test.gguf"
            )
        ]
        
        api_keys = {}  # No API keys needed for local models
        
        missing = _check_required_api_keys(models, api_keys)
        assert len(missing) == 0


class TestCLIIntegration:
    """Test CLI integration scenarios."""
    
    def test_cli_help_messages(self):
        """Test that all commands have proper help messages."""
        runner = CliRunner()
        
        # Test main CLI help
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Evaluate creativity of LLMs" in result.output
        
        # Test evaluate command help
        result = runner.invoke(cli, ['evaluate', '--help'])
        assert result.exit_code == 0
        assert "Run LLM creativity evaluation" in result.output
        assert "--config" in result.output
        assert "--dry-run" in result.output
        assert "--resume" in result.output
        
        # Test validate command help
        result = runner.invoke(cli, ['validate', '--help'])
        assert result.exit_code == 0
        assert "Validate configuration files" in result.output
        
        # Test clean command help
        result = runner.invoke(cli, ['clean', '--help'])
        assert result.exit_code == 0
        assert "Clean up cached files and models" in result.output


if __name__ == "__main__":
    # Run tests manually for debugging
    pytest.main([__file__, "-v"])
