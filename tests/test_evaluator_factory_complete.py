"""Test evaluator factory with comprehensive dependency mocking."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys


class TestEvaluatorFactoryComplete:
    """Complete test coverage for EvaluatorFactory with mocked dependencies."""
    
    def setup_method(self):
        """Set up mocks before each test method."""
        self.mock_modules = {
            'anthropic': MagicMock(),
            'torch': MagicMock(),
            'transformers': MagicMock(),
            'langchain_community': MagicMock(),
            'langchain_core': MagicMock(),
            'src.storybench.unified_context_system': MagicMock(),
            'src.storybench.langchain_context_manager': MagicMock(),
        }
        
        self.module_patcher = patch.dict('sys.modules', self.mock_modules)
        self.module_patcher.start()
        
        self.mock_modules['src.storybench.unified_context_system'].UnifiedContextManager = MagicMock()
        self.mock_modules['src.storybench.unified_context_system'].ContextLimitExceededError = Exception
        self.mock_modules['src.storybench.unified_context_system'].ContextConfig = MagicMock()
        self.mock_modules['src.storybench.langchain_context_manager'].ContextStrategy = MagicMock()
        self.mock_modules['src.storybench.langchain_context_manager'].ContextStrategy.PRESERVE_ALL = 'PRESERVE_ALL'
    
    def teardown_method(self):
        """Clean up mocks after each test."""
        self.module_patcher.stop()
    
    def test_create_api_evaluator(self):
        """Test creating API evaluator."""
        from src.storybench.evaluators.factory import EvaluatorFactory
        
        config = {"type": "api", "provider": "openai", "model_name": "gpt-4"}
        api_keys = {"openai": "test-key"}
        
        with patch('src.storybench.evaluators.factory.APIEvaluator') as mock_api:
            mock_instance = Mock()
            mock_api.return_value = mock_instance
            
            result = EvaluatorFactory.create_evaluator("test-model", config, api_keys)
            
            mock_api.assert_called_once_with("test-model", config, api_keys)
            assert result == mock_instance

    def test_create_local_evaluator(self):
        """Test creating local evaluator."""
        from src.storybench.evaluators.factory import EvaluatorFactory
        
        config = {"type": "local", "model_path": "/path/to/model"}
        api_keys = {}
        
        with patch('src.storybench.evaluators.factory.LocalEvaluator') as mock_local:
            mock_instance = Mock()
            mock_local.return_value = mock_instance
            
            result = EvaluatorFactory.create_evaluator("test-model", config, api_keys)
            
            mock_local.assert_called_once_with("test-model", config)
            assert result == mock_instance
    
    def test_create_evaluator_unsupported_type(self):
        """Test creating evaluator with unsupported type."""
        from src.storybench.evaluators.factory import EvaluatorFactory
        
        config = {"type": "unsupported"}
        api_keys = {}
        
        with pytest.raises(ValueError, match="Unsupported model type: unsupported"):
            EvaluatorFactory.create_evaluator("test", config, api_keys)
    
    def test_create_evaluator_empty_type(self):
        """Test creating evaluator with empty type."""
        from src.storybench.evaluators.factory import EvaluatorFactory
        
        config = {"type": ""}
        api_keys = {}
        
        with pytest.raises(ValueError, match="Unsupported model type: "):
            EvaluatorFactory.create_evaluator("test", config, api_keys)
    
    def test_create_evaluator_no_type(self):
        """Test creating evaluator with no type specified."""
        from src.storybench.evaluators.factory import EvaluatorFactory
        
        config = {}
        api_keys = {}
        
        with pytest.raises(ValueError, match="Unsupported model type: "):
            EvaluatorFactory.create_evaluator("test", config, api_keys)
    
    def test_create_evaluator_case_insensitive(self):
        """Test that type matching is case insensitive."""
        from src.storybench.evaluators.factory import EvaluatorFactory
        
        config = {"type": "API"}
        api_keys = {"openai": "test-key"}
        
        with patch('src.storybench.evaluators.factory.APIEvaluator') as mock_api:
            mock_instance = Mock()
            mock_api.return_value = mock_instance
            
            result = EvaluatorFactory.create_evaluator("test", config, api_keys)
            
            mock_api.assert_called_once_with("test", config, api_keys)
            assert result == mock_instance
