"""LiteLLM-based evaluator for unified API access across providers."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
import litellm
from litellm import acompletion, ModelResponse
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from .base import BaseEvaluator
from ..unified_context_system import ContextLimitExceededError

logger = logging.getLogger(__name__)

# Configure LiteLLM settings
litellm.drop_params = True  # Drop unsupported params instead of failing
litellm.set_verbose = False  # Set to True for debugging


class LiteLLMEvaluator(BaseEvaluator):
    """
    Evaluator using LiteLLM for unified API access across providers.
    Maintains LangChain for context management (no truncation policy).
    """
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize LiteLLM evaluator with configuration.
        
        Args:
            name: Evaluator name
            config: Model configuration including provider, model_name, etc.
            api_keys: Dictionary of API keys by provider
        """
        super().__init__(name, config)
        
        self.provider = config.get("provider", "").lower()
        self.model_name = config.get("model_name", "")
        self.api_keys = api_keys
        
        # Validate required configuration
        if not self.provider or not self.model_name:
            raise ValueError(f"LiteLLM evaluator {name} missing provider or model_name")
        
        # Setup LiteLLM model string and configuration
        self.litellm_model = self._construct_litellm_model_string()
        self._configure_litellm()
        
        # Track usage for logging
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        
        logger.info(f"Initialized LiteLLMEvaluator for {self.litellm_model}")
    
    def _construct_litellm_model_string(self) -> str:
        """Construct the model string for LiteLLM based on provider.
        
        Returns:
            Properly formatted model string for LiteLLM
        """
        # LiteLLM model string formatting by provider
        if self.provider == "openai":
            # OpenAI models use direct names
            return self.model_name
            
        elif self.provider == "anthropic":
            # Anthropic models use direct names
            return self.model_name
            
        elif self.provider == "google":
            # Gemini models need gemini/ prefix
            if self.model_name.startswith("gemini"):
                return f"gemini/{self.model_name}"
            else:
                return f"vertex_ai/{self.model_name}"
                
        elif self.provider == "deepinfra":
            # DeepInfra uses deepinfra/ prefix
            return f"deepinfra/{self.model_name}"
            
        else:
            # Default format: provider/model
            return f"{self.provider}/{self.model_name}"
    
    def _configure_litellm(self):
        """Configure LiteLLM with provider-specific settings."""
        # Set API keys based on provider
        if self.provider == "openai":
            api_key = self.api_keys.get("openai")
            if api_key:
                litellm.openai_api_key = api_key
                import os
                os.environ["OPENAI_API_KEY"] = api_key
                
        elif self.provider == "anthropic":
            api_key = self.api_keys.get("anthropic")
            if api_key:
                litellm.anthropic_api_key = api_key
                import os
                os.environ["ANTHROPIC_API_KEY"] = api_key
                
        elif self.provider == "google":
            # For Google/Gemini via API (not Vertex)
            api_key = self.api_keys.get("gemini") or self.api_keys.get("google")
            if api_key:
                import os
                os.environ["GEMINI_API_KEY"] = api_key
                
        elif self.provider == "deepinfra":
            # DeepInfra configuration
            api_key = self.api_keys.get("deepinfra")
            if api_key:
                import os
                os.environ["DEEPINFRA_API_KEY"] = api_key
                # DeepInfra uses OpenAI-compatible endpoint
                litellm.api_base = "https://api.deepinfra.com/v1"
        
        # Set custom headers if needed
        if self.provider == "deepinfra":
            litellm.headers = {"X-Provider": "deepinfra"}
    
    async def setup(self) -> bool:
        """Test LiteLLM connectivity with the configured model.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info(f"Testing LiteLLM setup for {self.litellm_model}")
            
            # Simple connectivity test
            test_messages = [{"role": "user", "content": "Hello, please respond with 'OK'."}]
            
            response = await acompletion(
                model=self.litellm_model,
                messages=test_messages,
                max_tokens=10,
                temperature=0.0,
                timeout=30.0
            )
            
            if response and response.choices:
                logger.info(f"✅ LiteLLM setup successful for {self.litellm_model}")
                return True
            else:
                logger.error(f"❌ No response from {self.litellm_model}")
                return False
                
        except Exception as e:
            logger.error(f"❌ LiteLLM setup failed for {self.litellm_model}: {str(e)}")
            if "api_key" in str(e).lower():
                logger.error(f"API key issue for {self.provider}. Check your .env file.")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((
            litellm.exceptions.RateLimitError,
            litellm.exceptions.APIConnectionError,
            litellm.exceptions.APIError,
            litellm.exceptions.ServiceUnavailableError,
            litellm.exceptions.Timeout
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _generate_with_retry(self, messages: List[Dict], **kwargs) -> ModelResponse:
        """Generate response with retry logic.
        
        Args:
            messages: Chat messages
            **kwargs: Additional arguments for completion
            
        Returns:
            Model response from LiteLLM
        """
        return await acompletion(
            model=self.litellm_model,
            messages=messages,
            **kwargs
        )
    
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 1.0,
        max_tokens: int = 8192,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using LiteLLM with LangChain context management.
        
        This method:
        1. Uses LangChain to build context (NO TRUNCATION)
        2. Generates response via LiteLLM's unified API
        3. Updates context history
        4. Returns response in standard format
        
        Args:
            prompt: The prompt text
            temperature: Generation temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary with response and metadata
            
        Raises:
            ContextLimitExceededError: If context exceeds model limits
        """
        start_time = time.time()
        
        try:
            # Step 1: Build context using LangChain (preserves full history)
            context = self.context_manager.build_context(
                history_text=self.generation_history,
                current_prompt=prompt
            )
            
            # Get context statistics
            context_stats = self.context_manager.get_context_stats(context)
            logger.info(
                f"Context: {context_stats['estimated_tokens']}/{context_stats['max_tokens']} tokens "
                f"({context_stats['token_utilization']:.1%} utilization)"
            )
            
            # Step 2: Prepare messages for LiteLLM
            messages = [{"role": "user", "content": context}]
            
            # Step 3: Prepare completion parameters
            completion_kwargs = {
                "temperature": temperature,
                "timeout": 300.0,  # 5 minute timeout
            }
            
            # Handle provider-specific parameters
            if self.provider == "openai" and self.model_name.startswith(("o3", "o4")):
                # o3/o4 models use max_completion_tokens
                completion_kwargs["max_completion_tokens"] = max_tokens
            else:
                completion_kwargs["max_tokens"] = max_tokens
            
            # Add any additional kwargs (e.g., top_p, frequency_penalty)
            completion_kwargs.update(kwargs)
            
            # Step 4: Generate response with retry logic
            logger.debug(f"Generating with {self.litellm_model}, temp={temperature}, max_tokens={max_tokens}")
            
            response = await self._generate_with_retry(
                messages=messages,
                **completion_kwargs
            )
            
            # Step 5: Extract response content
            response_text = response.choices[0].message.content
            
            # Handle None content (some models may return None for certain inputs)
            if response_text is None:
                response_text = ""
                logger.warning(f"Model {self.litellm_model} returned None content")
            
            # Step 6: Update generation history for next turn
            self.generation_history = context + "\n\n" + response_text
            
            # Step 7: Calculate metrics
            generation_time = time.time() - start_time
            
            # Update usage tracking
            if hasattr(response, 'usage') and response.usage:
                self.total_prompt_tokens += response.usage.prompt_tokens
                self.total_completion_tokens += response.usage.completion_tokens
                
                # Calculate cost if available
                try:
                    cost = litellm.completion_cost(
                        model=self.litellm_model,
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens
                    )
                    self.total_cost += cost
                except:
                    cost = None
            else:
                cost = None
            
            # Step 8: Prepare response in standard format
            result = {
                "response": response_text,
                "model": self.model_name,
                "provider": self.provider,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "generation_time": generation_time,
                "context_stats": context_stats,
                "litellm_model": self.litellm_model,
            }
            
            # Add usage stats if available
            if hasattr(response, 'usage') and response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cost": cost
                }
            
            logger.info(f"Generated {len(response_text)} chars in {generation_time:.2f}s")
            return result
            
        except ContextLimitExceededError:
            # Re-raise context errors without retry
            raise
            
        except litellm.exceptions.AuthenticationError as e:
            logger.error(f"Authentication failed for {self.provider}: {str(e)}")
            raise ValueError(f"Invalid API key for {self.provider}")
            
        except litellm.exceptions.NotFoundError as e:
            logger.error(f"Model not found: {self.litellm_model}")
            raise ValueError(f"Model {self.model_name} not found for {self.provider}")
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise
    
    async def cleanup(self):
        """Cleanup any resources (LiteLLM doesn't require explicit cleanup)."""
        # Log usage summary
        if self.total_completion_tokens > 0:
            logger.info(
                f"LiteLLM session summary for {self.name}: "
                f"Prompt tokens: {self.total_prompt_tokens:,}, "
                f"Completion tokens: {self.total_completion_tokens:,}, "
                f"Total cost: ${self.total_cost:.4f}"
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model configuration.
        
        Returns:
            Dictionary with model information
        """
        return {
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "litellm_model": self.litellm_model,
            "context_size": self.config.get("context_size", "unknown"),
            "total_tokens_used": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost": self.total_cost
        }


# Factory function for creating evaluators
def create_litellm_evaluator(
    name: str,
    provider: str,
    model_name: str,
    api_keys: Dict[str, str],
    context_size: Optional[int] = None,
    **kwargs
) -> LiteLLMEvaluator:
    """Factory function to create a LiteLLM evaluator.
    
    Args:
        name: Evaluator name
        provider: Provider name (openai, anthropic, google, deepinfra)
        model_name: Model identifier
        api_keys: Dictionary of API keys
        context_size: Maximum context size in tokens
        **kwargs: Additional configuration
        
    Returns:
        Configured LiteLLMEvaluator instance
    """
    config = {
        "provider": provider,
        "model_name": model_name,
        **kwargs
    }
    
    if context_size:
        config["context_size"] = context_size
    
    return LiteLLMEvaluator(name, config, api_keys)
