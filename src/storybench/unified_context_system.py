"""Unified context management with single source of truth for limits."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from langchain_community.llms import LlamaCpp
    from langchain_core.callbacks import CallbackManagerForLLMRun
except ImportError:
    raise ImportError(
        "LangChain packages not found. Please install: "
        "pip install langchain-community langchain-core"
    )

from .langchain_context_manager import ContextConfig, LangChainContextManager

logger = logging.getLogger(__name__)


class ContextLimitExceededError(Exception):
    """Raised when context exceeds the configured limit."""
    pass


class UnifiedContextManager(LangChainContextManager):
    """
    Context manager that enforces strict limits and never truncates.
    
    This is the single source of truth for context limits.
    """
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """Initialize with strict no-truncation policy."""
        if config is None:
            config = ContextConfig()
        
        # Force PRESERVE_ALL strategy - we handle limits ourselves
        config.strategy = config.strategy  # Keep user's choice but we'll override behavior
        
        super().__init__(config)
        
        # We are the authority on context limits
        self.max_context_tokens = config.max_context_tokens
        
        logger.info(f"Unified context manager: {self.max_context_tokens} token limit (strict, no truncation)")
    
    def build_context(
        self,
        history_text: str = "",
        current_prompt: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build context with strict limit enforcement.
        
        Raises ContextLimitExceededError if context would exceed limits.
        """
        if not current_prompt:
            raise ValueError("Current prompt cannot be empty")
        
        # Handle empty history case
        if not history_text:
            logger.debug("No history provided, using current prompt only")
            final_context = current_prompt
        else:
            # Build the full context
            final_context = self._format_final_context(history_text, current_prompt)
        
        # Check token limit BEFORE returning
        estimated_tokens = self._estimate_tokens(final_context)
        
        if estimated_tokens > self.max_context_tokens:
            raise ContextLimitExceededError(
                f"Context exceeds limit: {estimated_tokens} tokens > {self.max_context_tokens} max. "
                f"Context length: {len(final_context)} characters. "
                f"Consider using a model with larger context window or reducing input size."
            )
        
        logger.info(f"Context built successfully: {estimated_tokens}/{self.max_context_tokens} tokens")
        return final_context
    
    def check_context_size(self, text: str) -> Dict[str, Any]:
        """Check if text fits within context limits.
        
        Returns:
            Dictionary with size info and whether it fits
        """
        estimated_tokens = self._estimate_tokens(text)
        fits = estimated_tokens <= self.max_context_tokens
        
        return {
            "estimated_tokens": estimated_tokens,
            "max_tokens": self.max_context_tokens,
            "fits": fits,
            "utilization": estimated_tokens / self.max_context_tokens,
            "characters": len(text)
        }
    
    def get_max_context_tokens(self) -> int:
        """Get the authoritative context limit."""
        return self.max_context_tokens


class UnifiedLlamaCppWrapper(LlamaCpp):
    """
    LLM wrapper that inherits context limits from context manager.
    
    Single source of truth - no separate context limit configuration.
    """
    
    def __init__(
        self,
        model_path: str,
        context_manager: UnifiedContextManager,
        name: str = "Unified-LlamaCpp",
        n_batch: int = 512,
        n_threads: Optional[int] = None,
        temperature: float = 0.8,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        repeat_penalty: float = 1.1,
        **kwargs
    ):
        """Initialize LLM wrapper with context manager as source of truth.
        
        Args:
            model_path: Path to the GGUF model file
            context_manager: The context manager (source of truth for limits)
            name: Display name for the model
            n_batch: Batch size for processing
            n_threads: Number of threads (auto-detected if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate (output limit)
            top_p: Top-p sampling
            repeat_penalty: Repetition penalty
            **kwargs: Additional arguments for LlamaCpp
        """
        self.model_name = name
        self.model_path = Path(model_path)
        self.context_manager = context_manager
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Get context size from context manager (single source of truth)
        n_ctx = context_manager.get_max_context_tokens()
        
        # Initialize parent class with inherited context size
        super().__init__(
            model_path=str(model_path),
            n_ctx=n_ctx,  # Inherited from context manager
            n_batch=n_batch,
            n_threads=n_threads,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            verbose=False,
            **kwargs
        )
        
        logger.info(f"Initialized {name} with inherited context size: {n_ctx} tokens")
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Generate response with context limit validation."""
        # Validate context size before generation
        size_info = self.context_manager.check_context_size(prompt)
        
        if not size_info["fits"]:
            raise ContextLimitExceededError(
                f"Input prompt exceeds model context limit: "
                f"{size_info['estimated_tokens']} tokens > {size_info['max_tokens']} max"
            )
        
        # Proceed with generation
        return super().__call__(prompt, **kwargs)
    
    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return "unified-llamacpp"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "name": self.model_name,
            "model_path": str(self.model_path),
            "context_size": self.n_ctx,  # Inherited from context manager
            "batch_size": self.n_batch,
            "threads": self.n_threads,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_manager_max": self.context_manager.get_max_context_tokens()
        }


def create_unified_system(
    model_path: str,
    max_context_tokens: int = 32000,
    model_name: Optional[str] = None,
    **llm_kwargs
) -> tuple[UnifiedContextManager, UnifiedLlamaCppWrapper]:
    """
    Create a unified context management system with single source of truth.
    
    Args:
        model_path: Path to the GGUF model file
        max_context_tokens: Maximum context tokens (32K, 128K, 256K, 1M, etc.)
        model_name: Display name for the model
        **llm_kwargs: Additional arguments for the LLM wrapper
        
    Returns:
        Tuple of (context_manager, llm_wrapper) with shared configuration
    """
    # Create context configuration
    config = ContextConfig(
        max_context_tokens=max_context_tokens,
        chunk_size=min(8000, max_context_tokens // 8),  # Scale appropriately
        chunk_overlap=min(400, max_context_tokens // 80)
    )
    
    # Create context manager (source of truth)
    context_manager = UnifiedContextManager(config)
    
    # Create LLM wrapper that inherits from context manager
    if model_name is None:
        model_name = f"Model-{max_context_tokens//1000}K"
    
    llm_wrapper = UnifiedLlamaCppWrapper(
        model_path=model_path,
        context_manager=context_manager,
        name=model_name,
        **llm_kwargs
    )
    
    logger.info(f"Created unified system: {max_context_tokens} tokens, no truncation")
    
    return context_manager, llm_wrapper


# Convenience functions for different model sizes
def create_32k_system(model_path: str, **kwargs):
    """Create unified system for 32K models."""
    return create_unified_system(model_path, 32000, "Gemma-3-32K", **kwargs)


def create_128k_system(model_path: str, **kwargs):
    """Create unified system for 128K models."""
    return create_unified_system(model_path, 128000, "Gemma-3-128K", **kwargs)


def create_1m_system(model_path: str, **kwargs):
    """Create unified system for 1M+ models."""
    return create_unified_system(model_path, 1000000, "Future-1M", **kwargs)
