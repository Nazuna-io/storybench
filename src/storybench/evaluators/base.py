"""Abstract base class for all LLM evaluators."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from datetime import datetime


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
        
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a response to the given prompt.
        
        Args:
            prompt: The input prompt text
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing:
                - response: The generated text
                - generation_time: Time taken in seconds
                - completed_at: ISO timestamp
                - metadata: Additional model-specific data
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
        
    def _create_response_dict(self, response_text: str, start_time: float, 
                             metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Helper to create standardized response dictionary.
        
        Args:
            response_text: The generated text response
            start_time: Start time from time.time()
            metadata: Optional additional metadata
            
        Returns:
            Standardized response dictionary
        """
        generation_time = time.time() - start_time
        return {
            "response": response_text,
            "generation_time": generation_time,
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
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
            "model_name": self.config.get("model_name", "unknown")
        }
