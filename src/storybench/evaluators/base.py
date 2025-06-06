"""Abstract base class for all LLM evaluators."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from datetime import datetime

from ..unified_context_system import UnifiedContextManager, ContextLimitExceededError


class BaseEvaluator(ABC):
    """Abstract base class defining the interface for all LLM evaluators."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the evaluator with name and configuration.
        
        Args:
            name: Display name for the model
            config: Model-specific configuration dictionary
        """
        self.name = name
        self.config = config
        self.is_setup = False
        
        # Initialize context manager with appropriate size
        context_size = config.get('context_size', 32768)  # Default to 32K
        
        from ..unified_context_system import ContextConfig
        from ..langchain_context_manager import ContextStrategy
        context_config = ContextConfig(
            max_context_tokens=context_size,
            strategy=ContextStrategy.PRESERVE_ALL  # No truncation policy
        )
        self.context_manager = UnifiedContextManager(context_config)
        
        # Initialize generation history for context accumulation
        self.generation_history = ""
        
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a response to the given prompt with context validation.
        
        Args:
            prompt: The input prompt text
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing:
                - response: The generated text
                - generation_time: Time taken in seconds
                - completed_at: ISO timestamp
                - metadata: Additional model-specific data
                - context_stats: Context usage statistics
                
        Raises:
            ContextLimitExceededError: If prompt exceeds context limits
        """
        pass
        
    @abstractmethod
    async def setup(self) -> bool:
        """Setup the evaluator (load model, test API connection, etc.).
        
        Returns:
            True if setup successful, False otherwise
        """
        pass        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources (unload model, close connections, etc.)."""
        pass
    
    def validate_context_size(self, prompt: str) -> Dict[str, Any]:
        """Validate that prompt fits within context limits.
        
        For creative writing evaluations, this monitors context size but allows
        the model to handle its own limits naturally. No exceptions raised.
        
        Args:
            prompt: The prompt text to validate
            
        Returns:
            Dictionary with context statistics (warnings instead of errors)
        """
        # Use flexible validation that warns but doesn't fail
        return self.context_manager.validate_context_size_strict(prompt, f"evaluator_{self.name}")
    
    def monitor_sequence_context(self, sequence_name: str, prompt_index: int, accumulated_context: str) -> Dict[str, Any]:
        """Monitor context growth within a sequence for creative writing.
        
        Args:
            sequence_name: Name of the current sequence  
            prompt_index: Index of current prompt in sequence
            accumulated_context: Full accumulated context
            
        Returns:
            Dictionary with sequence context analytics
        """
        return self.context_manager.monitor_sequence_context_growth(
            sequence_name, prompt_index, accumulated_context
        )
    
    def get_context_analytics(self, prompt: str) -> Dict[str, Any]:
        """Get detailed context analytics for evaluation reports.
        
        Args:
            prompt: The prompt text to analyze
            
        Returns:
            Dictionary with detailed context analytics
        """
        return self.context_manager.get_context_analytics(prompt)
    
    def get_context_limits(self) -> Dict[str, int]:
        """Get context limits for this evaluator.
        
        Returns:
            Dictionary with context size information
        """
        return {
            'max_context_tokens': self.context_manager.max_context_tokens,
            'strategy': 'PRESERVE_ALL'  # We enforce strict no-truncation
        }
    
    def reset_context(self):
        """Reset the generation history/context.
        
        This is used between sequences to ensure clean context for coherence testing.
        """
        self.generation_history = ""
        
    def _create_response_dict(self, response_text: str, start_time: float, 
                             metadata: Optional[Dict] = None,
                             context_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """Helper to create standardized response dictionary.
        
        Args:
            response_text: The generated text response
            start_time: Start time from time.time()
            metadata: Optional additional metadata
            context_stats: Optional context usage statistics
            
        Returns:
            Standardized response dictionary
        """
        generation_time = time.time() - start_time
        return {
            "response": response_text,
            "generation_time": generation_time,
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {},
            "context_stats": context_stats or {}
        }
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about this model.
        
        Returns:
            Dictionary with model type, name, and configuration
        """
        return {
            "name": self.name,
            "type": self.config.get("type", "unknown"),
            "provider": self.config.get("provider", "unknown"),
            "model_name": self.config.get("model_name", "unknown"),
            "context_limits": self.get_context_limits()
        }
