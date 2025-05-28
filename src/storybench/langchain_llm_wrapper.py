"""LangChain LLM wrapper for local GGUF models."""

import logging
from typing import Dict, Any, Optional, List, Iterator, AsyncIterator
from pathlib import Path

try:
    from langchain_community.llms import LlamaCpp
    from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
    from langchain_core.language_models.llms import LLM
    from langchain_core.outputs import GenerationChunk
except ImportError:
    raise ImportError(
        "LangChain packages not found. Please install: "
        "pip install langchain-community langchain-core"
    )

logger = logging.getLogger(__name__)


class StorybenchLlamaCppWrapper(LlamaCpp):
    """
    Custom LangChain wrapper for Storybench GGUF models.
    
    Extends LangChain's LlamaCpp with Storybench-specific configurations
    and optimizations for large context handling.
    """
    
    def __init__(
        self,
        model_path: str,
        name: str = "Storybench-LlamaCpp",
        n_ctx: int = 32768,  # Gemma 3 context size
        n_batch: int = 512,
        n_threads: Optional[int] = None,
        temperature: float = 0.8,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        repeat_penalty: float = 1.1,
        **kwargs
    ):
        """Initialize the Storybench LlamaCpp wrapper."""
        self.model_name = name
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Initialize parent class with Storybench optimizations
        super().__init__(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_threads=n_threads,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            verbose=False,  # Reduce verbose output
            **kwargs
        )
        
        logger.info(f"Initialized {name} with context size: {n_ctx}")
    
    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return "storybench-llamacpp"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "name": self.model_name,
            "model_path": str(self.model_path),
            "context_size": self.n_ctx,
            "batch_size": self.n_batch,
            "threads": self.n_threads,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


def create_langchain_llm(
    model_path: str,
    model_name: str = "Gemma-3",
    context_size: int = 32768,
    **kwargs
) -> StorybenchLlamaCppWrapper:
    """
    Factory function to create a LangChain-wrapped LLM for Storybench.
    
    Args:
        model_path: Path to the GGUF model file
        model_name: Display name for the model
        context_size: Maximum context size
        **kwargs: Additional arguments for the wrapper
        
    Returns:
        Configured StorybenchLlamaCppWrapper instance
    """
    return StorybenchLlamaCppWrapper(
        model_path=model_path,
        name=model_name,
        n_ctx=context_size,
        **kwargs
    )
