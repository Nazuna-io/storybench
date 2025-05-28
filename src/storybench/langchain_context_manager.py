"""LangChain-based context management for large context handling without truncation."""

import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
    from langchain_core.documents import Document
except ImportError:
    raise ImportError(
        "LangChain packages not found. Please install: "
        "pip install langchain langchain-core langchain-community"
    )

logger = logging.getLogger(__name__)


class ContextStrategy(Enum):
    """Strategy for handling large contexts."""
    PRESERVE_ALL = "preserve_all"  # No truncation, use full context
    SMART_SPLIT = "smart_split"    # Split intelligently but preserve meaning
    SLIDING_WINDOW = "sliding_window"  # Use sliding window for very large contexts


@dataclass
class ContextConfig:
    """Configuration for context management."""
    max_context_tokens: int = 32000  # Gemma 3 default, scalable
    chunk_size: int = 4000
    chunk_overlap: int = 200
    strategy: ContextStrategy = ContextStrategy.PRESERVE_ALL
    preserve_structure: bool = True
    add_context_markers: bool = True



class LangChainContextManager:
    """
    LangChain-based context manager that handles large contexts without truncation.
    
    Designed to replace the custom context manager with LangChain's robust
    text processing capabilities while supporting contexts up to 32K tokens
    and beyond.
    """
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """Initialize the LangChain context manager.
        
        Args:
            config: Context configuration. Uses defaults if None.
        """
        self.config = config or ContextConfig()
        
        # Initialize text splitters
        self._init_text_splitters()
        
        logger.info(f"LangChain context manager initialized with {self.config.max_context_tokens} max tokens")
    
    def _init_text_splitters(self):
        """Initialize LangChain text splitters."""
        # Recursive character splitter for general text processing
        self.char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        
        # Token-based splitter for precise token control
        # Note: This will be configured with specific tokenizer in production
        self.token_splitter = TokenTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        
        logger.debug("Text splitters initialized")
    
    def build_context(
        self,
        history_text: str = "",
        current_prompt: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build context for LLM input, preserving full content without truncation.
        
        Args:
            history_text: Previous conversation/generation history
            current_prompt: Current prompt to be processed
            metadata: Optional metadata for context processing
            
        Returns:
            Complete context string ready for LLM input
        """
        if not current_prompt:
            raise ValueError("Current prompt cannot be empty")
        
        # Handle empty history case
        if not history_text:
            logger.debug("No history provided, using current prompt only")
            return self._format_final_context("", current_prompt)
        
        # Estimate total tokens
        total_content = f"{history_text}\n\n{current_prompt}"
        estimated_tokens = self._estimate_tokens(total_content)
        
        logger.info(f"Processing context: ~{estimated_tokens} tokens, max: {self.config.max_context_tokens}")
        
        # Apply strategy based on content size
        if estimated_tokens <= self.config.max_context_tokens:
            # Content fits within limits - preserve everything
            logger.debug("Full context fits within token limits")
            return self._format_final_context(history_text, current_prompt)
        
        elif self.config.strategy == ContextStrategy.PRESERVE_ALL:
            # Force preservation even if over limit - let model handle it
            logger.warning(f"Context exceeds limits ({estimated_tokens} > {self.config.max_context_tokens}) but preserving all")
            return self._format_final_context(history_text, current_prompt)
        
        elif self.config.strategy == ContextStrategy.SMART_SPLIT:
            # Use intelligent splitting to preserve meaning
            return self._smart_split_context(history_text, current_prompt)
        
        elif self.config.strategy == ContextStrategy.SLIDING_WINDOW:
            # Use sliding window approach
            return self._sliding_window_context(history_text, current_prompt)
        
        else:
            raise ValueError(f"Unknown context strategy: {self.config.strategy}")
    
    def build_context(
        self,
        history_text: str = "",
        current_prompt: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build context for LLM input, preserving full content without truncation.
        
        Args:
            history_text: Previous conversation/generation history
            current_prompt: Current prompt to be processed
            metadata: Optional metadata for context processing
            
        Returns:
            Complete context string ready for LLM input
        """
        if not current_prompt:
            raise ValueError("Current prompt cannot be empty")
        
        # Handle empty history case
        if not history_text:
            logger.debug("No history provided, using current prompt only")
            return self._format_final_context("", current_prompt)
        
        # Estimate total tokens
        total_content = f"{history_text}\n\n{current_prompt}"
        estimated_tokens = self._estimate_tokens(total_content)
        
        logger.info(f"Processing context: ~{estimated_tokens} tokens, max: {self.config.max_context_tokens}")
        
        # Apply strategy based on content size
        if estimated_tokens <= self.config.max_context_tokens:
            # Content fits within limits - preserve everything
            logger.debug("Full context fits within token limits")
            return self._format_final_context(history_text, current_prompt)
        
        elif self.config.strategy == ContextStrategy.PRESERVE_ALL:
            # Force preservation even if over limit - let model handle it
            logger.warning(f"Context exceeds limits ({estimated_tokens} > {self.config.max_context_tokens}) but preserving all")
            return self._format_final_context(history_text, current_prompt)
        
        elif self.config.strategy == ContextStrategy.SMART_SPLIT:
            # Use intelligent splitting to preserve meaning
            return self._smart_split_context(history_text, current_prompt)
        
        elif self.config.strategy == ContextStrategy.SLIDING_WINDOW:
            # Use sliding window approach
            return self._sliding_window_context(history_text, current_prompt)
        
        else:
            raise ValueError(f"Unknown context strategy: {self.config.strategy}")
    
    def _format_final_context(self, history: str, prompt: str) -> str:
        """Format the final context string."""
        if not history:
            return prompt
        
        separator = "\n\n---\n\n" if self.config.add_context_markers else "\n\n"
        
        if self.config.add_context_markers:
            return f"{history}{separator}{prompt}"
        else:
            return f"{history}{separator}{prompt}"
    
    def _smart_split_context(self, history_text: str, current_prompt: str) -> str:
        """
        Intelligently split and preserve the most relevant context.
        
        This method uses LangChain's text splitters to create meaningful chunks
        while preserving as much context as possible.
        """
        # Reserve tokens for current prompt and formatting
        prompt_tokens = self._estimate_tokens(current_prompt)
        formatting_tokens = 50  # Buffer for separators and markers
        available_for_history = self.config.max_context_tokens - prompt_tokens - formatting_tokens
        
        if available_for_history <= 0:
            logger.warning("Current prompt too long, using prompt only")
            return current_prompt
        
        # Split history into manageable chunks
        history_docs = self.char_splitter.create_documents([history_text])
        
        # Select chunks that fit within available tokens, prioritizing recent content
        selected_chunks = []
        used_tokens = 0
        
        # Start from the end (most recent) and work backwards
        for doc in reversed(history_docs):
            chunk_tokens = self._estimate_tokens(doc.page_content)
            if used_tokens + chunk_tokens <= available_for_history:
                selected_chunks.insert(0, doc.page_content)  # Insert at beginning to maintain order
                used_tokens += chunk_tokens
            else:
                break
        
        if selected_chunks:
            preserved_history = "\n\n".join(selected_chunks)
            if len(selected_chunks) < len(history_docs):
                # Add truncation marker if we couldn't fit everything
                preserved_history = f"[...earlier content omitted...]\n\n{preserved_history}"
            
            logger.info(f"Smart split preserved {len(selected_chunks)}/{len(history_docs)} chunks (~{used_tokens} tokens)")
            return self._format_final_context(preserved_history, current_prompt)
        else:
            logger.warning("No history chunks fit within token limits")
            return current_prompt
    
    def _sliding_window_context(self, history_text: str, current_prompt: str) -> str:
        """
        Use sliding window approach for very large contexts.
        
        This maintains a window of the most recent context that fits
        within the token limits.
        """
        # Reserve tokens for current prompt and formatting
        prompt_tokens = self._estimate_tokens(current_prompt)
        formatting_tokens = 50
        available_for_history = self.config.max_context_tokens - prompt_tokens - formatting_tokens
        
        if available_for_history <= 0:
            logger.warning("Current prompt too long, using prompt only")
            return current_prompt
        
        # Estimate how much history we can preserve
        history_chars = len(history_text)
        chars_per_token = 3.5  # Conservative estimate
        available_chars = int(available_for_history * chars_per_token)
        
        if history_chars <= available_chars:
            # All history fits
            return self._format_final_context(history_text, current_prompt)
        
        # Take the most recent portion that fits
        preserved_history = history_text[-available_chars:]
        
        # Try to start at a sentence boundary
        for boundary in ['\n\n', '. ', '! ', '? ', '\n']:
            boundary_pos = preserved_history.find(boundary)
            if 0 < boundary_pos < 500:  # Look within first 500 characters
                preserved_history = preserved_history[boundary_pos + len(boundary):]
                break
        
        preserved_history = f"[...earlier content in sliding window...]\n\n{preserved_history}"
        
        logger.info(f"Sliding window preserved {len(preserved_history)} chars from {history_chars} total")
        return self._format_final_context(preserved_history, current_prompt)
    
    def create_documents_from_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Create LangChain documents from text for advanced processing.
        
        Args:
            text: Input text to process
            metadata: Optional metadata to attach to documents
            
        Returns:
            List of LangChain Document objects
        """
        docs = self.char_splitter.create_documents([text], metadatas=[metadata] if metadata else None)
        logger.debug(f"Created {len(docs)} documents from text")
        return docs
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        This is a simple estimation. In production, this should use
        the actual tokenizer from the model being used.
        """
        # Conservative estimation: ~3.5 characters per token
        return int(len(text) / 3.5)
    
    def get_context_stats(self, context: str) -> Dict[str, Any]:
        """Get statistics about the context."""
        return {
            "character_count": len(context),
            "estimated_tokens": self._estimate_tokens(context),
            "max_tokens": self.config.max_context_tokens,
            "token_utilization": self._estimate_tokens(context) / self.config.max_context_tokens,
            "strategy": self.config.strategy.value
        }


# Convenience functions for backward compatibility
def build_langchain_context(
    history_text: str = "",
    current_prompt: str = "",
    max_tokens: int = 32000,
    strategy: ContextStrategy = ContextStrategy.PRESERVE_ALL
) -> str:
    """
    Convenience function for building context with LangChain.
    
    Args:
        history_text: Previous conversation/generation history
        current_prompt: Current prompt to be processed  
        max_tokens: Maximum tokens for context
        strategy: Context handling strategy
        
    Returns:
        Complete context string ready for LLM input
    """
    config = ContextConfig(
        max_context_tokens=max_tokens,
        strategy=strategy
    )
    manager = LangChainContextManager(config)
    return manager.build_context(history_text, current_prompt)


# For migration compatibility
def estimate_tokens_langchain(text: str) -> int:
    """Estimate tokens using LangChain approach."""
    return int(len(text) / 3.5)
