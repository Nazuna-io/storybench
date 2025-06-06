"""Enhanced API-based LLM evaluator with unified context management and retry logic."""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Tuple, Type

import openai
import anthropic
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .base import BaseEvaluator
from ..unified_context_system import ContextLimitExceededError
from ..utils.retry_handler import retry_handler

logger = logging.getLogger(__name__)

# Default context limits for different providers (tokens)
PROVIDER_CONTEXT_LIMITS = {
    'openai': {
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-turbo': 128000,
        'gpt-4o': 128000,
        'gpt-3.5-turbo': 4096,
        'gpt-3.5-turbo-16k': 16384,
    },
    'anthropic': {
        'claude-3-haiku': 200000,
        'claude-3-sonnet': 200000,
        'claude-3-opus': 200000,
        'claude-3.5-sonnet': 200000,
        'claude-3.5-haiku': 200000,
    },
    'gemini': {
        'gemini-pro': 30720,
        'gemini-1.5-pro': 1000000,
        'gemini-1.5-flash': 1000000,
    },
    'deepinfra': {
        'deepseek-ai/DeepSeek-R1': 128000,
        'deepseek-ai/DeepSeek-R1-0528': 128000,
        'deepseek-ai/DeepSeek-R1-Turbo': 128000,
        'meta-llama/Meta-Llama-3-70B-Instruct': 8192,
        'meta-llama/Meta-Llama-3-8B-Instruct': 8192,
        'mistralai/Mistral-7B-Instruct-v0.1': 32768,
        'Qwen/Qwen2.5-72B-Instruct': 32768,
    }
}


class APIEvaluator(BaseEvaluator):
    """Enhanced evaluator for API-based LLM services with context management."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize API evaluator with context management."""
        # Determine context size before calling super().__init__
        provider = config.get("provider", "").lower()
        model_name = config.get("model_name", "")
        
        # Set context size based on model capabilities or config override
        if "context_size" in config:
            context_size = config["context_size"]
        else:
            # Determine from provider and model
            context_size = self._get_default_context_size(provider, model_name)
        
        # Add context_size to config for parent initialization
        config["context_size"] = context_size
        
        super().__init__(name, config)
        
        self.api_keys = api_keys
        self.provider = provider
        self.model_name = model_name
        self.client = None
        
        # Validate configuration
        if not self.provider or not self.model_name:
            raise ValueError(f"API model {name} missing required configuration: provider and model_name")
        
        api_key = self.api_keys.get(self.provider)
        if not api_key and self.provider != "gemini":  # Gemini might use different auth
            raise ValueError(f"API model {name} missing API key for provider {self.provider}")
    
    def _get_default_context_size(self, provider: str, model_name: str) -> int:
        """Get default context size for a provider/model combination."""
        provider_limits = PROVIDER_CONTEXT_LIMITS.get(provider, {})
        
        # Try exact match first
        if model_name in provider_limits:
            return provider_limits[model_name]
        
        # Try partial matches for model families
        for model_key, limit in provider_limits.items():
            if model_key in model_name or model_name.startswith(model_key):
                return limit
        
        # Default fallback - conservative 32K
        logger.warning(f"Unknown model {model_name} for provider {provider}, defaulting to 32K context")
        return 32768
    
    async def setup(self) -> bool:
        """Setup API clients and test connectivity."""
        try:
            logger.info(f"Setting up APIEvaluator for {self.name} ({self.provider})")
            
            if self.provider == "openai":
                self.client = openai.AsyncOpenAI(api_key=self.api_keys.get("openai"))
                # Test with a minimal request
                if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
                    await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": "Test"}],
                        max_completion_tokens=10
                    )
                else:
                    await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=1
                    )
                
            elif self.provider == "anthropic":
                self.client = anthropic.AsyncAnthropic(api_key=self.api_keys.get("anthropic"))
                # Test with a minimal request
                await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "Test"}]
                )
                
            elif self.provider == "gemini":
                genai.configure(api_key=self.api_keys.get("gemini"))
                self.client = genai.GenerativeModel(self.model_name)
                # Test with a minimal request
                response = await self.client.generate_content_async("Test")
                
            elif self.provider == "deepinfra":
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_keys.get("deepinfra"),
                    base_url="https://api.deepinfra.com/v1/openai"
                )
                # Test with a minimal request
                if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
                    await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": "Test"}],
                        max_completion_tokens=10
                    )
                else:
                    await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=1
                    )
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            self.is_setup = True
            logger.info(f"APIEvaluator {self.name} setup complete with {self.context_manager.max_context_tokens} token context")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup APIEvaluator {self.name}: {e}")
            return False
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using the appropriate API with context validation."""
        if not self.is_setup:
            raise RuntimeError(f"Evaluator {self.name} not setup")

        start_time = time.time()
        
        try:
            # STRICT CONTEXT VALIDATION - No truncation allowed
            context_stats = self.validate_context_size(prompt)
            
            # Get detailed analytics for evaluation reports
            context_analytics = self.get_context_analytics(prompt)
            logger.info(f"Context validation passed for {self.name}: "
                       f"hash={context_analytics['prompt_hash']}, "
                       f"tokens={context_analytics['estimated_tokens']}/{context_analytics['max_tokens']}, "
                       f"utilization={context_analytics['utilization_percent']:.1f}%")
            
            max_retries = kwargs.get("max_retries", 3)
            base_delay = 1  # seconds
            
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    if self.provider == "openai":
                        response_text = await self._generate_openai(prompt, **kwargs)
                    elif self.provider == "anthropic":
                        response_text = await self._generate_anthropic(prompt, **kwargs)
                    elif self.provider == "gemini":
                        response_text = await self._generate_gemini(prompt, **kwargs)
                    elif self.provider == "deepinfra":
                        response_text = await self._generate_deepinfra(prompt, **kwargs)
                    else:
                        raise ValueError(f"Unsupported provider: {self.provider}")
                    
                    # Success - return response with enhanced context analytics
                    metadata = {
                        "model_name": self.model_name,
                        "provider": self.provider,
                        "attempts": attempt + 1
                    }
                    
                    return self._create_response_dict(
                        response_text, 
                        start_time, 
                        metadata=metadata,
                        context_stats=context_analytics
                    )

                except OPENAI_NON_RETRYABLE_ERRORS as e:
                    if self.provider in ["openai", "deepinfra"]:
                        logger.error(f"Non-retryable {self.provider} error for {self.name}: {type(e).__name__} - {e}")
                        last_exception = e
                        break 
                except ANTHROPIC_NON_RETRYABLE_ERRORS as e:
                    if self.provider == "anthropic":
                        logger.error(f"Non-retryable Anthropic error for {self.name}: {type(e).__name__} - {e}")
                        last_exception = e
                        break
                except GEMINI_NON_RETRYABLE_ERRORS as e:
                    if self.provider == "gemini":
                        logger.error(f"Non-retryable Gemini error for {self.name}: {type(e).__name__} - {e}")
                        last_exception = e
                        break
                
                except OPENAI_RETRYABLE_EXCEPTIONS as e:
                    if self.provider in ["openai", "deepinfra"]:
                        last_exception = e
                        if attempt < max_retries:
                            delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                            logger.warning(f"Retryable {self.provider} error for {self.name}: {type(e).__name__} - {e}. Retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"Max retries reached for {self.provider} error: {type(e).__name__} - {e}")
                            break
                    else:
                        raise
                except ANTHROPIC_RETRYABLE_EXCEPTIONS as e:
                    if self.provider == "anthropic":
                        last_exception = e
                        if attempt < max_retries:
                            delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                            logger.warning(f"Retryable Anthropic error for {self.name}: {type(e).__name__} - {e}. Retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"Max retries reached for Anthropic error: {type(e).__name__} - {e}")
                            break
                    else:
                        raise
                except GEMINI_RETRYABLE_EXCEPTIONS as e:
                    if self.provider == "gemini":
                        last_exception = e
                        if attempt < max_retries:
                            delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                            logger.warning(f"Retryable Gemini error for {self.name}: {type(e).__name__} - {e}. Retrying in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"Max retries reached for Gemini error: {type(e).__name__} - {e}")
                            break
                    else:
                        raise
                
                except Exception as e:
                    logger.error(f"Unexpected error for {self.name} ({self.provider}): {type(e).__name__} - {e}")
                    last_exception = e
                    break

            # If all retries failed or a non-retryable error occurred
            error_msg = f"Error generating response after {max_retries + 1} attempts: {type(last_exception).__name__} - {str(last_exception)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
                    
        except ContextLimitExceededError:
            # Re-raise context errors without modification
            raise
        except Exception as e:
            logger.error(f"Failed to generate response for {self.name}: {type(e).__name__} - {e}")
            raise
    
    async def _generate_with_provider(self, prompt: str, **kwargs) -> str:
        """Route to appropriate provider-specific generation method."""
        if self.provider == "openai":
            return await self._generate_openai(prompt, **kwargs)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt, **kwargs)
        elif self.provider == "gemini":
            return await self._generate_gemini(prompt, **kwargs)
        elif self.provider == "deepinfra":
            return await self._generate_deepinfra(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def cleanup(self) -> None:
        """Clean up API connections."""
        try:
            if self.client:
                # Close any persistent connections
                if hasattr(self.client, 'close'):
                    await self.client.close()
            self.client = None
            self.is_setup = False
            logger.info(f"APIEvaluator {self.name} cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup for {self.name}: {e}")
    
    async def _generate_openai(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        
        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0
        }
        
        # Use appropriate token parameter based on model
        if self.model_name.startswith("o3") or self.model_name.startswith("o4"):
            request_params["max_completion_tokens"] = kwargs.get("max_completion_tokens", kwargs.get("max_tokens", 4096))
        else:
            request_params["max_tokens"] = kwargs.get("max_tokens", 4096)
        
        response = await self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    
    async def _generate_anthropic(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API."""
        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=1 if (self.model_name.startswith("o4")) else 1.0,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _generate_gemini(self, prompt: str, **kwargs) -> str:
        """Generate response using Gemini API."""
        response = await self.client.generate_content_async(prompt)
        return response.text
    
    async def _generate_deepinfra(self, prompt: str, **kwargs) -> str:
        """Generate response using DeepInfra API (OpenAI-compatible)."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=1 if (self.model_name.startswith("o4")) else 1.0,
            max_tokens=kwargs.get("max_tokens", 4096)
        )
        raw_content = response.choices[0].message.content
        
        # Filter thinking text for DeepSeek-R1 models
        if "deepseek-ai/DeepSeek-R1" in self.model_name:
            return self._filter_thinking_text(raw_content)
        
        return raw_content
    
    def _filter_thinking_text(self, content: str) -> str:
        """Remove thinking/reasoning traces from DeepSeek-R1 model responses."""
        import re
        
        # Remove content between <think> and </think> tags
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        # Remove content between <thinking> and </thinking> tags  
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
        
        # Remove content between [Thinking] and [/Thinking] markers
        content = re.sub(r'\[Thinking\].*?\[/Thinking\]', '', content, flags=re.DOTALL)
        
        # Remove content that starts with "I need to think about this..." patterns
        content = re.sub(r'^(I need to think.*?)\n\n', '', content, flags=re.MULTILINE | re.DOTALL)
        
        # Clean up multiple newlines and trim whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content
