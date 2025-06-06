"""
Comprehensive tests for evaluators/factory.py
These tests cover the EvaluatorFactory with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the factory we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the problematic dependencies before importing
sys.modules['storybench.unified_context_system'] = MagicMock()
sys.modules['storybench.langchain_context_manager'] = MagicMock()

from storybench.evaluators.factory import EvaluatorFactory


class TestEvaluatorFactory:
    """Test the EvaluatorFactory class."""
    
    @patch('storybench.evaluators.factory.APIEvaluator')
    def test_create_api_evaluator(self, mock_api_evaluator):
        """Test creating an API evaluator."""
        # Setup
        name = "gpt-4"
        config = {
            "type": "api",
            "provider": "openai",
            "model_name": "gpt-4"
        }
        api_keys = {"openai": "test_key"}
        
        mock_instance = Mock()
        mock_api_evaluator.return_value = mock_instance
        
        # Execute
        result = EvaluatorFactory.create_evaluator(name, config, api_keys)
        
        # Verify
        assert result == mock_instance
        mock_api_evaluator.assert_called_once_with(name, config, api_keys)
    
    @patch('storybench.evaluators.factory.LocalEvaluator')
    def test_create_local_evaluator(self, mock_local_evaluator):
        """Test creating a local evaluator."""
        # Setup
        name = "llama-7b"
        config = {
            "type": "local",
            "model_path": "/path/to/model",
            "context_size": 4096
        }
        api_keys = {}
        
        mock_instance = Mock()
        mock_local_evaluator.return_value = mock_instance
        
        # Execute
        result = EvaluatorFactory.create_evaluator(name, config, api_keys)
        
        # Verify
        assert result == mock_instance
        mock_local_evaluator.assert_called_once_with(name, config)
    
    @patch('storybench.evaluators.factory.APIEvaluator')
    def test_create_api_evaluator_case_insensitive(self, mock_api_evaluator):
        """Test that factory is case insensitive for model types."""
        # Setup
        name = "gpt-4"
        config = {
            "type": "API",  # Uppercase
            "provider": "openai"
        }
        api_keys = {"openai": "test_key"}
        
        mock_instance = Mock()
        mock_api_evaluator.return_value = mock_instance
        
        # Execute
        result = EvaluatorFactory.create_evaluator(name, config, api_keys)
        
        # Verify
        assert result == mock_instance
        mock_api_evaluator.assert_called_once_with(name, config, api_keys)
    
    def test_create_evaluator_unsupported_type(self):
        """Test that unsupported model type raises ValueError."""
        # Setup
        name = "unknown-model"
        config = {
            "type": "unsupported_type",
            "some_param": "value"
        }
        api_keys = {}
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Unsupported model type: unsupported_type"):
            EvaluatorFactory.create_evaluator(name, config, api_keys)
    
    def test_create_evaluator_missing_type(self):
        """Test that missing model type defaults to empty string and raises error."""
        # Setup
        name = "no-type-model"
        config = {
            "provider": "some_provider"
            # No "type" field
        }
        api_keys = {}
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Unsupported model type: "):
            EvaluatorFactory.create_evaluator(name, config, api_keys)
    
    @patch('storybench.evaluators.factory.LocalEvaluator')
    def test_create_local_evaluator_case_variations(self, mock_local_evaluator):
        """Test various case combinations for local model type."""
        mock_instance = Mock()
        mock_local_evaluator.return_value = mock_instance
        
        test_cases = ["local", "LOCAL", "Local", "LoCAL"]
        
        for model_type in test_cases:
            config = {"type": model_type}
            result = EvaluatorFactory.create_evaluator("test", config, {})
            assert result == mock_instance
        
        # Verify it was called for each test case
        assert mock_local_evaluator.call_count == len(test_cases)


class TestEvaluatorFactoryEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_factory_static_method_accessibility(self):
        """Test that factory method can be called without instantiation."""
        # Verify the method exists and is static
        assert hasattr(EvaluatorFactory, 'create_evaluator')
        assert callable(EvaluatorFactory.create_evaluator)
        
        # Should be able to call without creating instance
        with pytest.raises(ValueError):  # Will fail due to unsupported type, but method is callable
            EvaluatorFactory.create_evaluator("test", {"type": "invalid"}, {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
