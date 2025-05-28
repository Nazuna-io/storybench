"""Tests for LangChain context management."""

import pytest
from typing import Dict, Any
import logging

# Import our new LangChain components
from storybench.langchain_context_manager import (
    LangChainContextManager,
    ContextConfig,
    ContextStrategy,
    build_langchain_context,
    estimate_tokens_langchain
)

logger = logging.getLogger(__name__)


class TestLangChainContextManager:
    """Test suite for LangChain-based context management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.default_config = ContextConfig()
        self.manager = LangChainContextManager(self.default_config)
        
        # Test content samples
        self.short_prompt = "What is the weather today?"
        self.medium_text = "This is a medium-length text. " * 100  # ~3K chars
        self.long_text = "This is a very long text for testing large contexts. " * 1000  # ~50K chars
    
    def test_manager_initialization(self):
        """Test that the context manager initializes correctly."""
        assert self.manager.config.max_context_tokens == 32000
        assert self.manager.config.strategy == ContextStrategy.PRESERVE_ALL
        assert hasattr(self.manager, 'char_splitter')
        assert hasattr(self.manager, 'token_splitter')
    
    def test_empty_history_context(self):
        """Test context building with empty history."""
        result = self.manager.build_context(
            history_text="",
            current_prompt=self.short_prompt
        )
        assert result == self.short_prompt
    
    def test_smart_split_strategy(self):
        """Test SMART_SPLIT strategy."""
        config = ContextConfig(
            max_context_tokens=1000,  # Small limit to trigger splitting
            strategy=ContextStrategy.SMART_SPLIT
        )
        manager = LangChainContextManager(config)
        
        result = manager.build_context(
            history_text=self.long_text,
            current_prompt=self.short_prompt
        )
        
        # Should contain prompt and some history
        assert self.short_prompt in result
        # Should be shorter than original due to splitting
        assert len(result) < len(self.long_text) + len(self.short_prompt)
    
    def test_convenience_function(self):
        """Test the convenience build_langchain_context function."""
        result = build_langchain_context(
            history_text=self.medium_text,
            current_prompt=self.short_prompt,
            max_tokens=32000
        )
        
        assert self.medium_text in result
        assert self.short_prompt in result
    
    def test_context_stats(self):
        """Test context statistics generation."""
        context = self.manager.build_context(
            history_text=self.medium_text,
            current_prompt=self.short_prompt
        )
        
        stats = self.manager.get_context_stats(context)
        
        assert "character_count" in stats
        assert "estimated_tokens" in stats
        assert "max_tokens" in stats
        assert "token_utilization" in stats
        assert "strategy" in stats
        assert stats["character_count"] > 0
        assert stats["estimated_tokens"] > 0


class TestConvenienceFunctions:
    """Test convenience functions for backward compatibility."""
    
    def test_estimate_tokens_langchain(self):
        """Test token estimation function."""
        text = "This is a test sentence with some words."
        tokens = estimate_tokens_langchain(text)
        
        # Should be reasonable estimate
        assert tokens > 0
        assert tokens < len(text)  # Should be less than character count


class TestTextSplitting:
    """Test LangChain text splitting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = LangChainContextManager()
        self.long_document = """
        Chapter 1: The Beginning
        
        This is the start of our story. It was a dark and stormy night.
        The protagonist was sitting by the fire, reading a book.
        
        Chapter 2: The Adventure
        
        The next day, our hero embarked on a great adventure.
        They traveled through forests and over mountains.
        
        Chapter 3: The Conclusion
        
        After many trials, the hero finally reached their destination.
        The story ended happily ever after.
        """ * 50  # Make it large enough to require splitting
    
    def test_document_creation(self):
        """Test creating LangChain documents from text."""
        docs = self.manager.create_documents_from_text(
            self.long_document,
            metadata={"source": "test_document"}
        )
        
        assert len(docs) > 1  # Should be split into multiple documents
        assert all(hasattr(doc, 'page_content') for doc in docs)
        assert all(hasattr(doc, 'metadata') for doc in docs)
