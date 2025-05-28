"""Enhanced context overflow handling for Storybench."""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from .langchain_context_manager import LangChainContextManager, ContextConfig, ContextStrategy

logger = logging.getLogger(__name__)


class OverflowStrategy(Enum):
    """Strategies for handling context overflow."""
    FAIL_SAFE = "fail_safe"           # Fail gracefully with error
    AUTO_TRUNCATE = "auto_truncate"   # Intelligent truncation
    CHUNK_PROCESS = "chunk_process"   # Process in chunks
    COMPRESS = "compress"             # Compress/summarize content


class RobustContextManager(LangChainContextManager):
    """
    Enhanced context manager with robust overflow handling.
    
    Extends the base LangChain context manager with multiple strategies
    for handling contexts that exceed model limits.
    """
    
    def __init__(self, config: Optional[ContextConfig] = None, overflow_strategy: OverflowStrategy = OverflowStrategy.AUTO_TRUNCATE):
        """Initialize robust context manager.
        
        Args:
            config: Context configuration
            overflow_strategy: How to handle context overflow
        """
        super().__init__(config)
        self.overflow_strategy = overflow_strategy
        
        # Calculate safe margins
        self.safety_margin = int(self.config.max_context_tokens * 0.05)  # 5% safety margin
        self.effective_limit = self.config.max_context_tokens - self.safety_margin
        
        logger.info(f"Robust context manager: {self.config.max_context_tokens} max, "
                   f"{self.effective_limit} effective limit, overflow: {overflow_strategy.value}")
    
    def build_context_safe(
        self,
        history_text: str = "",
        current_prompt: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build context with overflow protection and detailed result info.
        
        Returns:
            Dictionary with context, status, and metadata
        """
        try:
            # First, try the normal build process
            context = self.build_context(history_text, current_prompt, metadata)
            estimated_tokens = self._estimate_tokens(context)
            
            # Check if we're within safe limits
            if estimated_tokens <= self.effective_limit:
                return {
                    "context": context,
                    "status": "success",
                    "tokens_used": estimated_tokens,
                    "tokens_available": self.config.max_context_tokens,
                    "overflow_handled": False,
                    "strategy_used": "none"
                }
            
            # Handle overflow based on strategy
            return self._handle_overflow(history_text, current_prompt, estimated_tokens, metadata)
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return self._emergency_fallback(current_prompt, str(e))
    
    def _handle_overflow(
        self, 
        history_text: str, 
        current_prompt: str, 
        estimated_tokens: int,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle context overflow based on configured strategy."""
        
        logger.warning(f"Context overflow detected: {estimated_tokens} > {self.effective_limit}")
        
        if self.overflow_strategy == OverflowStrategy.FAIL_SAFE:
            return {
                "context": current_prompt,  # Just the prompt
                "status": "overflow_error",
                "tokens_used": self._estimate_tokens(current_prompt),
                "tokens_available": self.config.max_context_tokens,
                "overflow_handled": True,
                "strategy_used": "fail_safe",
                "error": f"Context too large: {estimated_tokens} tokens > {self.effective_limit} limit"
            }
        
        elif self.overflow_strategy == OverflowStrategy.AUTO_TRUNCATE:
            # Use smart truncation
            truncated_context = self._smart_truncate(history_text, current_prompt)
            return {
                "context": truncated_context,
                "status": "overflow_truncated",
                "tokens_used": self._estimate_tokens(truncated_context),
                "tokens_available": self.config.max_context_tokens,
                "overflow_handled": True,
                "strategy_used": "auto_truncate"
            }
        
        elif self.overflow_strategy == OverflowStrategy.CHUNK_PROCESS:
            # Prepare for chunk processing
            chunks = self._prepare_chunks(history_text, current_prompt)
            return {
                "context": chunks[0] if chunks else current_prompt,  # First chunk
                "status": "overflow_chunked",
                "tokens_used": self._estimate_tokens(chunks[0]) if chunks else self._estimate_tokens(current_prompt),
                "tokens_available": self.config.max_context_tokens,
                "overflow_handled": True,
                "strategy_used": "chunk_process",
                "total_chunks": len(chunks),
                "chunks": chunks  # Return all chunks for processing
            }
        
        elif self.overflow_strategy == OverflowStrategy.COMPRESS:
            # Compress the context (placeholder for future implementation)
            compressed_context = self._compress_context(history_text, current_prompt)
            return {
                "context": compressed_context,
                "status": "overflow_compressed",
                "tokens_used": self._estimate_tokens(compressed_context),
                "tokens_available": self.config.max_context_tokens,
                "overflow_handled": True,
                "strategy_used": "compress"
            }
        
        else:
            # Fallback to truncation
            return self._handle_overflow(history_text, current_prompt, estimated_tokens, metadata)
    
    def _smart_truncate(self, history_text: str, current_prompt: str) -> str:
        """Intelligently truncate context to fit within limits."""
        # Reserve tokens for prompt and formatting
        prompt_tokens = self._estimate_tokens(current_prompt)
        formatting_tokens = 100  # Buffer for separators, etc.
        available_for_history = self.effective_limit - prompt_tokens - formatting_tokens
        
        if available_for_history <= 0:
            logger.warning("Current prompt too long for truncation, using prompt only")
            return current_prompt
        
        # Use character estimation to truncate history
        chars_per_token = 3.5
        available_chars = int(available_for_history * chars_per_token)
        
        if len(history_text) <= available_chars:
            return self._format_final_context(history_text, current_prompt)
        
        # Take the most recent portion
        truncated_history = history_text[-available_chars:]
        
        # Try to start at a natural boundary
        for boundary in ['\n\n---\n\n', '\n\n', '. ', '! ', '? ', '\n']:
            boundary_pos = truncated_history.find(boundary)
            if 0 < boundary_pos < 1000:  # Look within first 1000 chars
                truncated_history = truncated_history[boundary_pos + len(boundary):]
                break
        
        # Add truncation marker
        truncated_history = f"[...content truncated due to context limits...]\n\n{truncated_history}"
        
        result = self._format_final_context(truncated_history, current_prompt)
        logger.info(f"Smart truncation: {len(history_text)} -> {len(truncated_history)} chars")
        
        return result
    
    def _prepare_chunks(self, history_text: str, current_prompt: str) -> List[str]:
        """Prepare content for chunk processing."""
        # Split history into processable chunks
        docs = self.char_splitter.create_documents([history_text])
        
        chunks = []
        for i, doc in enumerate(docs):
            chunk_context = self._format_final_context(doc.page_content, current_prompt)
            if self._estimate_tokens(chunk_context) <= self.effective_limit:
                chunks.append(chunk_context)
            else:
                # This chunk is still too big, need further splitting
                logger.warning(f"Chunk {i} still too large, may need smaller chunk_size")
                chunks.append(self._smart_truncate(doc.page_content, current_prompt))
        
        logger.info(f"Prepared {len(chunks)} chunks for processing")
        return chunks
    
    def _compress_context(self, history_text: str, current_prompt: str) -> str:
        """Compress context (placeholder for future summarization)."""
        # TODO: Implement actual compression/summarization
        # For now, fall back to smart truncation
        logger.warning("Context compression not yet implemented, falling back to truncation")
        return self._smart_truncate(history_text, current_prompt)
    
    def _emergency_fallback(self, current_prompt: str, error: str) -> Dict[str, Any]:
        """Emergency fallback when everything else fails."""
        return {
            "context": current_prompt,
            "status": "emergency_fallback",
            "tokens_used": self._estimate_tokens(current_prompt),
            "tokens_available": self.config.max_context_tokens,
            "overflow_handled": True,
            "strategy_used": "emergency",
            "error": error
        }


def create_robust_context_manager(
    max_tokens: int = 32000,
    overflow_strategy: OverflowStrategy = OverflowStrategy.AUTO_TRUNCATE
) -> RobustContextManager:
    """Create a robust context manager with overflow handling.
    
    Args:
        max_tokens: Maximum context tokens (32K, 128K, 256K, 1M, etc.)
        overflow_strategy: How to handle overflow situations
        
    Returns:
        Configured RobustContextManager
    """
    config = ContextConfig(
        max_context_tokens=max_tokens,
        chunk_size=min(8000, max_tokens // 8),  # Scale chunk size appropriately
        chunk_overlap=min(400, max_tokens // 80),  # Scale overlap too
        strategy=ContextStrategy.PRESERVE_ALL  # Let overflow handler manage limits
    )
    
    return RobustContextManager(config, overflow_strategy)


# Quick configuration functions for different model sizes
def create_32k_context_manager(overflow_strategy: OverflowStrategy = OverflowStrategy.AUTO_TRUNCATE):
    """Create context manager for 32K models (Gemma 3 base)."""
    return create_robust_context_manager(32000, overflow_strategy)

def create_128k_context_manager(overflow_strategy: OverflowStrategy = OverflowStrategy.AUTO_TRUNCATE):
    """Create context manager for 128K models (Gemma 3 large)."""
    return create_robust_context_manager(128000, overflow_strategy)

def create_1m_context_manager(overflow_strategy: OverflowStrategy = OverflowStrategy.AUTO_TRUNCATE):
    """Create context manager for 1M+ models (future large models)."""
    return create_robust_context_manager(1000000, overflow_strategy)
