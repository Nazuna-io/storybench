"""Additional CLI tests for evaluate command and fixes."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from click.testing import CliRunner
import os
import tempfile
from pathlib import Path


class TestCLIEvaluate:
    """Test CLI evaluate command functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    @patch('src.storybench.cli._get_api_keys')
    @patch('src.storybench.cli._check_required_api_keys')
    def test_evaluate_dry_run(self, mock_check_keys, mock_get_keys, mock_config_class, mock_load_dotenv):
        """Test evaluate command with dry run flag."""
        from src.storybench.cli import cli
        
        # Mock configuration
        mock_config = Mock()
        mock_config.validate.return_value = []  # No errors
        mock_config.models = [Mock()]  # One model
        mock_config.prompts = {'seq1': ['prompt1']}  # One sequence
        mock_config_class.load_config.return_value = mock_config
        
        result = self.runner.invoke(cli, ['evaluate', '--config', 'test.yaml', '--dry-run'])
        
        assert result.exit_code == 0
        assert 'Configuration valid - 1 models, 1 prompt sequences' in result.output
        assert 'Dry run complete - configuration is valid' in result.output
        
        # Should not check API keys in dry run
        mock_get_keys.assert_not_called()
        mock_check_keys.assert_not_called()
    
    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    def test_evaluate_config_errors(self, mock_config_class, mock_load_dotenv):
        """Test evaluate command with configuration errors."""
        from src.storybench.cli import cli
        
        # Mock configuration with errors
        mock_config = Mock()
        mock_config.validate.return_value = ['Config error 1', 'Config error 2']
        mock_config_class.load_config.return_value = mock_config
        
        result = self.runner.invoke(cli, ['evaluate', '--config', 'test.yaml'])
        
        assert result.exit_code == 0
        assert 'Configuration errors:' in result.output
        assert 'Config error 1' in result.output
        assert 'Config error 2' in result.output

    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    @patch('src.storybench.cli._get_api_keys')
    @patch('src.storybench.cli._check_required_api_keys')
    def test_evaluate_missing_api_keys(self, mock_check_keys, mock_get_keys, mock_config_class, mock_load_dotenv):
        """Test evaluate command with missing API keys."""
        from src.storybench.cli import cli
        
        # Mock configuration
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.models = [Mock()]
        mock_config.prompts = {'seq1': ['prompt1']}
        mock_config_class.load_config.return_value = mock_config
        
        # Mock missing API keys
        mock_get_keys.return_value = {}
        mock_check_keys.return_value = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        
        result = self.runner.invoke(cli, ['evaluate', '--config', 'test.yaml'])
        
        assert result.exit_code == 0
        assert 'Missing required API keys:' in result.output
        assert 'OPENAI_API_KEY' in result.output
        assert 'ANTHROPIC_API_KEY' in result.output
        assert 'Please set these in your .env file' in result.output
    
    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    def test_evaluate_exception_handling(self, mock_config_class, mock_load_dotenv):
        """Test evaluate command exception handling."""
        from src.storybench.cli import cli
        
        # Mock configuration loading to raise exception
        mock_config_class.load_config.side_effect = Exception("Configuration error")
        
        result = self.runner.invoke(cli, ['evaluate', '--config', 'test.yaml'])
        
        assert result.exit_code == 0
        assert 'Error: Configuration error' in result.output
    
    @patch('src.storybench.cli.load_dotenv')
    @patch('src.storybench.cli.Config')
    @patch('src.storybench.cli._get_api_keys')
    @patch('src.storybench.cli._check_required_api_keys')
    @patch('src.storybench.cli.asyncio')
    def test_evaluate_success_path(self, mock_asyncio, mock_check_keys, mock_get_keys, mock_config_class, mock_load_dotenv):
        """Test evaluate command successful execution path."""
        from src.storybench.cli import cli
        
        # Mock configuration
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.models = [Mock()]
        mock_config.prompts = {'seq1': ['prompt1']}
        mock_config_class.load_config.return_value = mock_config
        
        # Mock API keys present
        mock_get_keys.return_value = {'OPENAI_API_KEY': 'sk-test'}
        mock_check_keys.return_value = []  # No missing keys
        
        # Mock asyncio.run
        mock_asyncio.run.return_value = None
        
        result = self.runner.invoke(cli, ['evaluate', '--config', 'test.yaml'])
        
        assert result.exit_code == 0
        mock_asyncio.run.assert_called_once()
