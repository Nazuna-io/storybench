"""Factory for creating evaluator instances."""

from typing import Dict, Any
from .base import BaseEvaluator
from .api_evaluator import APIEvaluator
from .local_evaluator import LocalEvaluator


class EvaluatorFactory:
    """Factory for creating the appropriate evaluator based on model type."""
    
    @staticmethod
    def create_evaluator(name: str, config: Dict[str, Any], 
                        api_keys: Dict[str, str]) -> BaseEvaluator:
        """Create an evaluator instance based on model configuration.
        
        Args:
            name: Display name for the model
            config: Model configuration dictionary
            api_keys: Dictionary of API keys
            
        Returns:
            Appropriate evaluator instance
            
        Raises:
            ValueError: If model type is unsupported
        """
        model_type = config.get("type", "").lower()
        
        if model_type == "api":
            return APIEvaluator(name, config, api_keys)
        elif model_type == "local":
            return LocalEvaluator(name, config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
