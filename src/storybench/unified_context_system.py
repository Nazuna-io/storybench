"""Unified context management with single source of truth for limits."""

import logging
import hashlib
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
    
    def validate_context_size_strict(self, text: str, context_name: str = "prompt") -> Dict[str, Any]:
        """Validate text fits within context limits with flexible enforcement.
        
        For creative writing evaluations, this provides monitoring and warnings
        but allows the model to handle its own context limits naturally.
        
        Args:
            text: The text to validate
            context_name: Descriptive name for logging (e.g., "prompt", "sequence_context")
            
        Returns:
            Dictionary with context statistics (never raises ContextLimitExceededError)
        """
        # Generate prompt fingerprint for traceability
        prompt_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        
        # Check context size
        stats = self.check_context_size(text)
        
        # Log context validation attempt
        logger.info(f"Context validation for {context_name} (hash: {prompt_hash}): "
                   f"{stats['estimated_tokens']}/{stats['max_tokens']} tokens "
                   f"({stats['utilization']:.1%} utilization)")
        
        if not stats['fits']:
            # WARNING ONLY - do not raise exception for creative writing evaluations
            # Models should handle their own context limits naturally
            warning_msg = (f"Context approaching/exceeding estimated limit for {context_name}: "
                          f"{stats['estimated_tokens']} tokens > {stats['max_tokens']} estimated max. "
                          f"Context length: {stats['characters']} characters. "
                          f"Hash: {prompt_hash}. "
                          f"Model will handle context limit naturally - continuing evaluation.")
            logger.warning(warning_msg)
            
            # Mark as over limit but don't fail
            stats['over_limit_warning'] = True
            stats['warning_message'] = warning_msg
        else:
            stats['over_limit_warning'] = False
        
        # Add fingerprint to stats for tracking
        stats['prompt_hash'] = prompt_hash
        stats['context_name'] = context_name
        stats['utilization_percent'] = stats['utilization'] * 100
        
        logger.debug(f"Context validation completed for {context_name} (hash: {prompt_hash})")
        return stats
    
    def monitor_sequence_context_growth(self, 
                                       sequence_name: str,
                                       prompt_index: int, 
                                       accumulated_context: str) -> Dict[str, Any]:
        """Monitor context growth within a sequence for creative writing evaluations.
        
        This provides detailed monitoring of how context accumulates within sequences
        without enforcing artificial limits that would break creative continuity.
        
        Args:
            sequence_name: Name of the current sequence
            prompt_index: Index of the current prompt in sequence (0, 1, 2, etc.)
            accumulated_context: Full accumulated context so far
            
        Returns:
            Dictionary with detailed context growth analytics
        """
        analytics = self.get_context_analytics(accumulated_context)
        
        # Enhanced logging for sequence context monitoring
        logger.info(f"Sequence context growth: {sequence_name} prompt {prompt_index + 1}: "
                   f"{analytics['estimated_tokens']} tokens "
                   f"({analytics['utilization_percent']:.1f}% of {analytics['max_tokens']} limit), "
                   f"hash: {analytics['prompt_hash']}")
        
        # Add sequence-specific metadata
        analytics.update({
            'sequence_name': sequence_name,
            'prompt_index': prompt_index,
            'is_sequence_start': prompt_index == 0,
            'context_growth_stage': f"prompt_{prompt_index + 1}"
        })
        
        # Provide recommendations if getting close to limits
        if analytics['utilization_percent'] > 80:
            logger.warning(f"Sequence {sequence_name} context approaching 80% utilization "
                          f"({analytics['utilization_percent']:.1f}%) - monitor for model performance")
        elif analytics['utilization_percent'] > 95:
            logger.warning(f"Sequence {sequence_name} context near capacity "
                          f"({analytics['utilization_percent']:.1f}%) - model may truncate")
        
        return analytics
    
    def get_context_analytics(self, text: str) -> Dict[str, Any]:
        """Get detailed analytics about context usage for evaluation reports.
        
        Args:
            text: The text to analyze
            
        Returns:
            Detailed analytics dictionary
        """
        stats = self.check_context_size(text)
        prompt_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        
        return {
            **stats,
            'prompt_hash': prompt_hash,
            'remaining_tokens': stats['max_tokens'] - stats['estimated_tokens'],
            'utilization_percent': stats['utilization'] * 100,
            'word_count': len(text.split()),
            'line_count': text.count('\n') + 1,
            'efficiency_ratio': len(text) / stats['estimated_tokens'] if stats['estimated_tokens'] > 0 else 0
        }
    
    def get_max_context_tokens(self) -> int:
        """Get the authoritative context limit."""
        return self.max_context_tokens


class UnifiedLlamaCppWrapper:
    """
    LLM wrapper that uses composition with LangChain LlamaCpp instead of inheritance.
    
    This avoids Pydantic field validation issues while maintaining functionality.
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
        print(f"DEBUG: UnifiedLlamaCppWrapper.__init__ called with name={name}")
        
        self._display_name = name
        self.model_path = Path(model_path)
        self.context_manager = context_manager
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Get context size from context manager (single source of truth)
        n_ctx = context_manager.get_max_context_tokens()
        
        print(f"DEBUG: About to create LlamaCpp instance with n_ctx={n_ctx}")
        
        # Create internal LlamaCpp instance instead of inheriting
        try:
            print(f"DEBUG: Preparing LlamaCpp() with parameters:")
            print(f"  model_path: {str(model_path)}")
            print(f"  n_ctx: {n_ctx}")
            print(f"  n_batch: {n_batch}")
            print(f"  n_threads: {n_threads}")
            print(f"  temperature: {temperature}")
            print(f"  max_tokens: {max_tokens}")
            print(f"  top_p: {top_p}")
            print(f"  repeat_penalty: {repeat_penalty}")
            print(f"  kwargs: {kwargs}")
            
            self._llm = LlamaCpp(
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
            print(f"DEBUG: LlamaCpp() instance created successfully")
        except Exception as e:
            print(f"DEBUG: Error creating LlamaCpp instance: {e}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            raise
        
        logger.info(f"Initialized {name} with inherited context size: {n_ctx} tokens")
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Generate response to the given prompt."""
        # Validate context size before generation
        size_info = self.context_manager.check_context_size(prompt)
        
        if not size_info["fits"]:
            raise ContextLimitExceededError(
                f"Input prompt exceeds model context limit: "
                f"{size_info['estimated_tokens']} tokens > {size_info['max_tokens']} max"
            )
        
        # Use the internal LlamaCpp instance
        return self._llm(prompt, **kwargs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "name": self._display_name,
            "model_path": str(self.model_path),
            "context_size": self._llm.n_ctx,  # From internal LlamaCpp instance
            "batch_size": self._llm.n_batch,
            "temperature": self._llm.temperature,
            "max_tokens": self._llm.max_tokens,
            "context_manager_max": self.context_manager.get_max_context_tokens()
        }
    
    # Expose commonly used properties from the internal LlamaCpp instance
    @property
    def n_ctx(self):
        return self._llm.n_ctx
    
    @property
    def n_batch(self):
        return self._llm.n_batch
    
    @property
    def temperature(self):
        return self._llm.temperature
    
    @property
    def max_tokens(self):
        return self._llm.max_tokens


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
