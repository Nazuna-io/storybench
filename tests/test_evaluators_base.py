"""Test evaluator factory with mocked dependencies."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock the problematic imports
sys.modules['src.storybench.unified_context_system'] = MagicMock()
sys.modules['src.storybench.langchain_context_manager'] = MagicMock()

class MockContextLimitExceededError(Exception):
    pass

with patch.dict('sys.modules', {
    'src.storybench.unified_context_system': MagicMock(
        UnifiedContextManager=MagicMock,
        ContextLimitExceededError=MockContextLimitExceededError,
        ContextConfig=MagicMock
    ),
    'src.storybench.langchain_context_manager': MagicMock(
        ContextStrategy=MagicMock(PRESERVE_ALL='PRESERVE_ALL')
    )
}):
    from src.storybench.evaluators.factory import EvaluatorFactory


class TestEvaluatorFactory:
    """Test EvaluatorFactory functionality."""
    
    def test_create_api_evaluator(self):
        """Test creating API evaluator."""
        config = {"type": "api", "provider": "openai"}
        api_keys = {"openai": "test-key"}
        
        with patch('src.storybench.evaluators.factory.APIEvaluator') as mock_api:
            mock_instance = Mock()
            mock_api.return_value = mock_instance
            
            result = EvaluatorFactory.create_evaluator("test", config, api_keys)
            
            mock_api.assert_called_once_with("test", config, api_keys)
            assert result == mock_instance
    
    def test_create_local_evaluator(self):
        """Test creating local evaluator."""
        config = {"type": "local", "model_path": "/path/to/model"}
        api_keys = {}
        
        with patch('src.storybench.evaluators.factory.LocalEvaluator') as mock_local:
            mock_instance = Mock()
            mock_local.return_value = mock_instance
            
            result = EvaluatorFactory.create_evaluator("test", config, api_keys)
            
            mock_local.assert_called_once_with("test", config)
            assert result == mock_instance

    def test_create_evaluator_unsupported_type(self):
        """Test creating evaluator with unsupported type."""
        config = {"type": "unsupported"}
        api_keys = {}
        
        with pytest.raises(ValueError, match="Unsupported model type: unsupported"):
            EvaluatorFactory.create_evaluator("test", config, api_keys)
    
    def test_create_evaluator_no_type(self):
        """Test creating evaluator with no type specified."""
        config = {}
        api_keys = {}
        
        with pytest.raises(ValueError, match="Unsupported model type: "):
            EvaluatorFactory.create_evaluator("test", config, api_keys)
    
    def test_create_evaluator_case_insensitive(self):
        """Test that type matching is case insensitive."""
        config = {"type": "API"}
        api_keys = {"openai": "test-key"}
        
        with patch('src.storybench.evaluators.factory.APIEvaluator') as mock_api:
            mock_instance = Mock()
            mock_api.return_value = mock_instance
            
            result = EvaluatorFactory.create_evaluator("test", config, api_keys)
            
            mock_api.assert_called_once_with("test", config, api_keys)
            assert result == mock_instance
