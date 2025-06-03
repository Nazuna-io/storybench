"""Test CLI interface with comprehensive mocking."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from click.testing import CliRunner
import os
import tempfile
from pathlib import Path


class TestCLI:
    """Test CLI commands with mocked dependencies."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
        # Mock all the complex dependencies
        self.mock_modules = {
            'src.storybench.evaluators.factory': MagicMock(),
            'src.storybench.database.services.evaluation_runner': MagicMock(),
            'src.storybench.database.services.sequence_evaluation_service': MagicMock(),
            'src.storybench.database.repositories.criteria_repo': MagicMock(),
            'motor.motor_asyncio': MagicMock(),
            'tqdm': MagicMock(),
        }
        
        # Patch imports
        self.module_patcher = patch.dict('sys.modules', self.mock_modules)
        self.module_patcher.start()
        
    def teardown_method(self):
        """Clean up after tests."""
        self.module_patcher.stop()
    
    def test_cli_group_exists(self):
        """Test that CLI group exists and is callable."""
        from src.storybench.cli import cli
        
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'StorybenchLLM' in result.output
        assert 'evaluate' in result.output
        assert 'validate' in result.output
        assert 'clean' in result.output
    
    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    def test_validate_command_success(self, mock_config_class, mock_load_dotenv):
        """Test validate command with valid configuration."""
        from src.storybench.cli import cli
        
        # Mock configuration loading
        mock_config = Mock()
        mock_config.validate.return_value = []  # No errors
        mock_config_class.load_config.return_value = mock_config
        
        result = self.runner.invoke(cli, ['validate', '--config', 'test.yaml'])
        
        assert result.exit_code == 0
        assert '✓ Configuration is valid' in result.output
        mock_config_class.load_config.assert_called_once_with('test.yaml')

    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    def test_validate_command_with_errors(self, mock_config_class, mock_load_dotenv):
        """Test validate command with configuration errors."""
        from src.storybench.cli import cli
        
        # Mock configuration loading with errors
        mock_config = Mock()
        mock_config.validate.return_value = ['Error 1', 'Error 2']
        mock_config_class.load_config.return_value = mock_config
        
        result = self.runner.invoke(cli, ['validate', '--config', 'test.yaml'])
        
        assert result.exit_code == 0
        assert 'Configuration errors:' in result.output
        assert 'Error 1' in result.output
        assert 'Error 2' in result.output
    
    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    def test_validate_command_exception(self, mock_config_class, mock_load_dotenv):
        """Test validate command when configuration loading fails."""
        from src.storybench.cli import cli
        
        # Mock configuration loading to raise exception
        mock_config_class.load_config.side_effect = Exception("File not found")
        
        result = self.runner.invoke(cli, ['validate', '--config', 'missing.yaml'])
        
        assert result.exit_code == 0
        assert 'Error loading configuration: File not found' in result.output
    
    def test_clean_command_with_models(self):
        """Test clean command to remove model files."""
        from src.storybench.cli import cli
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock model files
            models_dir = Path(tmpdir) / "models"
            models_dir.mkdir()
            
            model_file1 = models_dir / "model1.gguf"
            model_file2 = models_dir / "model2.gguf"
            model_file1.touch()
            model_file2.touch()
            
            # Change to temp directory
            with patch('pathlib.Path') as mock_path:
                mock_path.return_value = models_dir.parent
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.glob.return_value = [model_file1, model_file2]
                
                result = self.runner.invoke(cli, ['clean', '--models'])
                
                assert result.exit_code == 0
                assert 'Local models cleaned' in result.output
    
    def test_clean_command_no_models_dir(self):
        """Test clean command when no models directory exists."""
        from src.storybench.cli import cli
        
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            result = self.runner.invoke(cli, ['clean', '--models'])
            
            assert result.exit_code == 0
            assert 'No models directory found' in result.output

    def test_get_api_keys(self):
        """Test _get_api_keys function."""
        from src.storybench.cli import _get_api_keys
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test123',
            'ANTHROPIC_API_KEY': 'ant-test456',
            'GOOGLE_API_KEY': 'google-test789'
        }):
            keys = _get_api_keys()
            
            assert keys['OPENAI_API_KEY'] == 'sk-test123'
            assert keys['ANTHROPIC_API_KEY'] == 'ant-test456'
            assert keys['GOOGLE_API_KEY'] == 'google-test789'
            assert keys['QWEN_API_KEY'] is None
            assert keys['AI21_API_KEY'] is None
    
    def test_check_required_api_keys(self):
        """Test _check_required_api_keys function."""
        from src.storybench.cli import _check_required_api_keys
        
        # Mock model objects
        openai_model = Mock()
        openai_model.type = 'api'
        openai_model.provider = 'openai'
        
        anthropic_model = Mock()
        anthropic_model.type = 'api'
        anthropic_model.provider = 'anthropic'
        
        local_model = Mock()
        local_model.type = 'local'
        
        models = [openai_model, anthropic_model, local_model]
        
        # Test with missing keys
        api_keys = {'OPENAI_API_KEY': 'sk-test'}
        missing = _check_required_api_keys(models, api_keys)
        
        assert 'ANTHROPIC_API_KEY' in missing
        assert 'OPENAI_API_KEY' not in missing
        assert len(missing) == 1
    
    def test_check_required_api_keys_all_present(self):
        """Test _check_required_api_keys with all keys present."""
        from src.storybench.cli import _check_required_api_keys
        
        # Mock model objects
        openai_model = Mock()
        openai_model.type = 'api'
        openai_model.provider = 'openai'
        
        models = [openai_model]
        api_keys = {'OPENAI_API_KEY': 'sk-test'}
        
        missing = _check_required_api_keys(models, api_keys)
        assert missing == []
    
    def test_check_required_api_keys_unknown_provider(self):
        """Test _check_required_api_keys with unknown provider."""
        from src.storybench.cli import _check_required_api_keys
        
        # Mock model with unknown provider
        unknown_model = Mock()
        unknown_model.type = 'api'
        unknown_model.provider = 'unknown_provider'
        
        models = [unknown_model]
        api_keys = {}
        
        missing = _check_required_api_keys(models, api_keys)
        assert missing == []  # Unknown providers don't require keys
