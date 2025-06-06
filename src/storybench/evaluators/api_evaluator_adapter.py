"""Backwards compatibility adapter for APIEvaluator to LiteLLMEvaluator migration."""

import logging
from typing import Dict, Any

from .litellm_evaluator import LiteLLMEvaluator

logger = logging.getLogger(__name__)


class APIEvaluatorAdapter(LiteLLMEvaluator):
    """
    Adapter class that provides APIEvaluator interface using LiteLLMEvaluator.
    
    This allows existing code using APIEvaluator to work with minimal changes.
    """
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize adapter with APIEvaluator-style configuration.
        
        This adapter translates APIEvaluator config to LiteLLMEvaluator format.
        """
        # Log migration
        logger.info(f"Using APIEvaluatorAdapter for {name} - consider migrating to LiteLLMEvaluator")
        
        # Initialize parent with same parameters
        super().__init__(name, config, api_keys)
        
    # The interface is already compatible - LiteLLMEvaluator was designed
    # to match APIEvaluator's interface. Additional compatibility methods
    # can be added here if needed.


# Convenience function to match existing usage patterns
def create_api_evaluator(
    name: str,
    provider: str,
    model_name: str,
    api_keys: Dict[str, str],
    **kwargs
) -> APIEvaluatorAdapter:
    """Create an evaluator using the old APIEvaluator pattern.
    
    This function provides backwards compatibility for code that
    creates evaluators using the old pattern.
    
    Args:
        name: Evaluator name
        provider: Provider name
        model_name: Model name
        api_keys: API keys dictionary
        **kwargs: Additional configuration
        
    Returns:
        APIEvaluatorAdapter instance (which is a LiteLLMEvaluator)
    """
    config = {
        "provider": provider,
        "model_name": model_name,
        **kwargs
    }
    
    return APIEvaluatorAdapter(name, config, api_keys)


# Alias for complete backwards compatibility
APIEvaluator = APIEvaluatorAdapter
