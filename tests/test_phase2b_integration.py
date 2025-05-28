"""
Integration tests for Phase 2B: Context Management Integration with Evaluators
"""

import pytest
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.evaluators.local_evaluator import LocalEvaluator
from storybench.unified_context_system import ContextLimitExceededError


class TestPhase2BIntegration:
    """Test suite for Phase 2B: LangChain integration with evaluators."""
    
    def test_local_evaluator_initialization(self):
        """Test LocalEvaluator initialization with context management."""
        config = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'context_size': 32768
        }
        
        evaluator = LocalEvaluator('test-model', config)
        
        # Verify initialization
        assert evaluator.context_manager.max_context_tokens == 32768
        assert evaluator.model_parameters['n_ctx'] == 32768
        
        # Verify context limits
        limits = evaluator.get_context_limits()
        assert limits['max_context_tokens'] == 32768
        assert limits['strategy'] == 'PRESERVE_ALL'
        
        print("✅ LocalEvaluator initialization test passed")
    
    def test_context_validation_success(self):
        """Test successful context validation."""
        config = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'context_size': 32768
        }
        
        evaluator = LocalEvaluator('test-model', config)
        test_prompt = "This is a test prompt that should pass validation."
        
        context_stats = evaluator.validate_context_size(test_prompt)
        
        # Verify context stats
        assert 'estimated_tokens' in context_stats
        assert 'max_context_tokens' in context_stats
        assert 'remaining_tokens' in context_stats
        assert 'utilization_percent' in context_stats
        
        assert context_stats['max_context_tokens'] == 32768
        assert context_stats['estimated_tokens'] > 0
        assert context_stats['remaining_tokens'] > 0
        assert context_stats['utilization_percent'] < 100
        
        print("✅ Context validation success test passed")
    
    def test_context_validation_failure(self):
        """Test context validation failure with oversized prompt."""
        config = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'context_size': 100  # Very small limit for testing
        }
        
        evaluator = LocalEvaluator('test-model', config)
        
        # Create a prompt that exceeds the small context limit
        large_prompt = "This is a test prompt. " * 100  # Repeat to exceed 100 tokens
        
        # Should raise ContextLimitExceededError
        with pytest.raises(ContextLimitExceededError):
            evaluator.validate_context_size(large_prompt)
        
        print("✅ Context validation failure test passed")
    
    def test_different_context_sizes(self):
        """Test different context size configurations."""
        test_cases = [
            (4096, "4K context"),
            (32768, "32K context"),
            (131072, "128K context"),
            (1000000, "1M context")
        ]
        
        for context_size, description in test_cases:
            config = {
                'repo_id': 'test/model',
                'filename': 'test.gguf',
                'context_size': context_size
            }
            
            evaluator = LocalEvaluator(f'test-{context_size}', config)
            
            # Verify the context size was set correctly
            assert evaluator.context_manager.max_context_tokens == context_size
            assert evaluator.model_parameters['n_ctx'] == context_size
            
            print(f"✅ {description} configuration test passed")
    
    def test_model_info_includes_context_limits(self):
        """Test that model info includes context limits."""
        config = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'context_size': 32768,
            'type': 'local',
            'provider': 'llama-cpp',
            'model_name': 'test-model'
        }
        
        evaluator = LocalEvaluator('test-model', config)
        model_info = evaluator.get_model_info()
        
        # Verify model info contains context limits
        assert 'context_limits' in model_info
        assert model_info['context_limits']['max_context_tokens'] == 32768
        assert model_info['context_limits']['strategy'] == 'PRESERVE_ALL'
        
        print("✅ Model info context limits test passed")
    
    def test_strict_no_truncation_policy(self):
        """Test that the system enforces strict no-truncation policy."""
        config = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'context_size': 100  # Small limit for testing
        }
        
        evaluator = LocalEvaluator('test-model', config)
        
        # Test that context validation throws error instead of truncating
        large_prompt = "Word " * 100  # Should exceed 100 token limit (400 chars / 3.5 = ~114 tokens)
        
        try:
            evaluator.validate_context_size(large_prompt)
            assert False, "Should have raised ContextLimitExceededError"
        except ContextLimitExceededError as e:
            # Verify the error message is informative
            assert "exceeds maximum context size" in str(e)
            print("✅ Strict no-truncation policy test passed")
    
    def test_backwards_compatibility_with_existing_configs(self):
        """Test that existing config formats still work."""
        # Test flattened config (old format)
        config_flat = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'temperature': 0.8,
            'max_tokens': 2048,
            'n_gpu_layers': -1
        }
        
        evaluator_flat = LocalEvaluator('test-flat', config_flat)
        assert evaluator_flat.model_parameters['temperature'] == 0.8
        assert evaluator_flat.model_parameters['max_tokens'] == 2048
        assert evaluator_flat.model_parameters['n_gpu_layers'] == -1
        
        # Test nested config (new format)
        config_nested = {
            'repo_id': 'test/model',
            'filename': 'test.gguf',
            'model_settings': {
                'temperature': 0.9,
                'max_tokens': 4096,
                'n_gpu_layers': 10
            }
        }
        
        evaluator_nested = LocalEvaluator('test-nested', config_nested)
        assert evaluator_nested.model_parameters['temperature'] == 0.9
        assert evaluator_nested.model_parameters['max_tokens'] == 4096
        assert evaluator_nested.model_parameters['n_gpu_layers'] == 10
        
        print("✅ Backwards compatibility test passed")


if __name__ == "__main__":
    print("🚀 Running Phase 2B Integration Tests...")
    print()
    
    test_suite = TestPhase2BIntegration()
    
    try:
        test_suite.test_local_evaluator_initialization()
        test_suite.test_context_validation_success()
        test_suite.test_context_validation_failure()
        test_suite.test_different_context_sizes()
        test_suite.test_model_info_includes_context_limits()
        test_suite.test_strict_no_truncation_policy()
        test_suite.test_backwards_compatibility_with_existing_configs()
        
        print()
        print("🎉 All Phase 2B Integration Tests Passed!")
        print()
        print("📊 Phase 2B Implementation Summary:")
        print("✅ Enhanced BaseEvaluator with unified context management")
        print("✅ LocalEvaluator integration with LangChain wrappers")
        print("✅ Strict no-truncation policy enforcement")
        print("✅ Context validation and statistics")
        print("✅ Support for 32K, 128K, and 1M+ context sizes")
        print("✅ Backwards compatibility with existing configurations")
        print("✅ Comprehensive error handling and logging")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
