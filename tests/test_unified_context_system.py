"""Tests for unified context system with strict no-truncation policy."""

import pytest
from storybench.unified_context_system import (
    UnifiedContextManager,
    UnifiedLlamaCppWrapper,
    ContextLimitExceededError,
    create_unified_system,
    create_32k_system
)
from storybench.langchain_context_manager import ContextConfig


class TestUnifiedContextSystem:
    """Test suite for unified context management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ContextConfig(max_context_tokens=1000)  # Small for testing
        self.context_manager = UnifiedContextManager(self.config)
        
        # Test content
        self.short_prompt = "What is the weather?"
        self.medium_text = "This is medium text. " * 50  # ~1K chars
        self.long_text = "This is very long text. " * 200  # ~4K chars
    
    def test_context_manager_initialization(self):
        """Test context manager initializes correctly."""
        assert self.context_manager.max_context_tokens == 1000
        assert isinstance(self.context_manager, UnifiedContextManager)
    
    def test_context_within_limits(self):
        """Test that context within limits works normally."""
        result = self.context_manager.build_context(
            history_text="Short history",
            current_prompt=self.short_prompt
        )
        
        assert "Short history" in result
        assert self.short_prompt in result
    
    def test_context_exceeds_limits_raises_error(self):
        """Test that exceeding context limits raises ContextLimitExceededError."""
        with pytest.raises(ContextLimitExceededError) as exc_info:
            self.context_manager.build_context(
                history_text=self.long_text,
                current_prompt=self.short_prompt
            )
        
        assert "Context exceeds limit" in str(exc_info.value)
        assert "tokens >" in str(exc_info.value)
    
    def test_check_context_size(self):
        """Test context size checking utility."""
        # Small text should fit
        result = self.context_manager.check_context_size(self.short_prompt)
        assert result["fits"] is True
        assert result["estimated_tokens"] > 0
        assert result["max_tokens"] == 1000
        
        # Large text should not fit
        result = self.context_manager.check_context_size(self.long_text)
        assert result["fits"] is False
        assert result["utilization"] > 1.0
    
    def test_get_max_context_tokens(self):
        """Test getting authoritative context limit."""
        assert self.context_manager.get_max_context_tokens() == 1000


class TestUnifiedSystem:
    """Test the complete unified system."""
    
    def test_create_unified_system(self):
        """Test creating unified system with proper inheritance."""
        # This would normally require a real model file
        # For testing, we'll mock it or test the configuration logic
        
        config = ContextConfig(max_context_tokens=2000)
        context_manager = UnifiedContextManager(config)
        
        # Test that context manager has correct limits
        assert context_manager.get_max_context_tokens() == 2000
        
        # Test size checking
        small_text = "Small text"
        large_text = "Large text " * 1000
        
        assert context_manager.check_context_size(small_text)["fits"] is True
        assert context_manager.check_context_size(large_text)["fits"] is False
    
    def test_convenience_functions_return_correct_limits(self):
        """Test that convenience functions set correct limits."""
        # We can't actually initialize without model files, but we can test the config
        from storybench.unified_context_system import ContextConfig
        
        # Test 32K config
        config_32k = ContextConfig(max_context_tokens=32000)
        manager_32k = UnifiedContextManager(config_32k)
        assert manager_32k.get_max_context_tokens() == 32000
        
        # Test 128K config  
        config_128k = ContextConfig(max_context_tokens=128000)
        manager_128k = UnifiedContextManager(config_128k)
        assert manager_128k.get_max_context_tokens() == 128000


class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_context_limit_exceeded_error_details(self):
        """Test that error provides useful information."""
        config = ContextConfig(max_context_tokens=100)  # Very small
        manager = UnifiedContextManager(config)
        
        large_text = "This is a large text that will exceed the limit. " * 20
        
        with pytest.raises(ContextLimitExceededError) as exc_info:
            manager.build_context(history_text=large_text, current_prompt="Prompt")
        
        error_msg = str(exc_info.value)
        assert "Context exceeds limit" in error_msg
        assert "tokens >" in error_msg
        assert "100 max" in error_msg
        assert "Consider using a model with larger context window" in error_msg
    
    def test_empty_prompt_raises_error(self):
        """Test that empty prompt raises appropriate error."""
        config = ContextConfig(max_context_tokens=1000)
        manager = UnifiedContextManager(config)
        
        with pytest.raises(ValueError) as exc_info:
            manager.build_context(history_text="History", current_prompt="")
        
        assert "Current prompt cannot be empty" in str(exc_info.value)


# Example usage test (would require actual model file)
def example_usage():
    """Example of how to use the unified system."""
    
    # For 32K model
    try:
        context_manager, llm = create_32k_system("/path/to/gemma-32k.gguf")
        
        # Build context - will raise error if too large
        context = context_manager.build_context(
            history_text="Long conversation history...",
            current_prompt="Current evaluation prompt"
        )
        
        # Generate response - will raise error if context too large
        response = llm(context)
        
        print(f"Success: Generated response with {len(context)} character context")
        
    except ContextLimitExceededError as e:
        print(f"Context too large: {e}")
        # Handle by reducing context size or using larger model
        
    except FileNotFoundError as e:
        print(f"Model file not found: {e}")


# Migration example for existing code
def migration_example():
    """Example of migrating from separate limits to unified system."""
    
    # OLD WAY (separate limits - error prone):
    # context_manager = LangChainContextManager(ContextConfig(max_context_tokens=32000))
    # llm = StorybenchLlamaCppWrapper(model_path="...", n_ctx=32768)  # Different limit!
    
    # NEW WAY (unified limits):
    context_manager, llm = create_32k_system("/path/to/model.gguf")
    
    # Now both components share the same limit automatically
    assert context_manager.get_max_context_tokens() == llm.n_ctx
    
    # Scaling up is just one parameter change:
    # context_manager, llm = create_128k_system("/path/to/larger-model.gguf")
