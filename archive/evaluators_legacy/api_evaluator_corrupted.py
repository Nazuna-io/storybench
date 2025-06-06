"""Enhanced API-based LLM evaluator with unified context management."""

import asyncio
import time
import random # For jitter
import logging
from typing import Dict, Any, Optional, Tuple, Type

import openai
import anthropic
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .base import BaseEvaluator
from ..unified_context_system import ContextLimitExceededError

logger = logging.getLogger(__name__)

# Define retryable exceptions for each provider if specific ones are known
# OpenAI specific retryable exceptions (example, adjust as needed)
OPENAI_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
)
# Anthropic specific retryable exceptions
ANTHROPIC_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    anthropic.RateLimitError,
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)
# Google Gemini specific retryable exceptions
GEMINI_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    google_exceptions.DeadlineExceeded,
    google_exceptions.ServiceUnavailable,
    google_exceptions.ResourceExhausted, # Can sometimes be a rate limit
    # google_exceptions.InternalServerError, # Covered by general ServiceUnavailable or others
)

# Non-retryable API errors (e.g., auth, invalid request)
OPENAI_NON_RETRYABLE_ERRORS: Tuple[Type[Exception], ...] = (
    openai.AuthenticationError,
    openai.PermissionDeniedError,
    openai.NotFoundError,
    openai.BadRequestError, # Typically for invalid inputs
    openai.UnprocessableEntityError, # e.g. content policy violation
)
ANTHROPIC_NON_RETRYABLE_ERRORS: Tuple[Type[Exception], ...] = (
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
    anthropic.NotFoundError,
    anthropic.BadRequestError,
)
GEMINI_NON_RETRYABLE_ERRORS: Tuple[Type[Exception], ...] = (
    google_exceptions.PermissionDenied,
    google_exceptions.NotFound,
    google_exceptions.InvalidArgument,
    google_exceptions.FailedPrecondition,
    google_exceptions.Unauthenticated,
)

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
    }
}


class APIEvaluator(BaseEvaluator):
    """Enhanced evaluator for API-based LLM services with context management."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize API evaluator with context management.
        
        Args:
            name: Display name for the model
            config: Model configuration containing:
                - provider: API provider (openai, anthropic, gemini)
                - model_name: Specific model name
                - context_size: Override default context size
            api_keys: Dictionary of API keys for different providers
        """
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
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            self.is_setup = True
            logger.info(f"APIEvaluator {self.name} setup complete with {self.context_manager.max_context_tokens} token context")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup APIEvaluator {self.name}: {e}")
            return False
                
            elif self.provider == "gemini":
                genai.configure(api_key=self.api_keys.get("google"))
                self.client = genai.GenerativeModel(self.model_name)
                await self._test_gemini_connection()
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            self.is_setup = True
            return True            
        except Exception as e:
            print(f"Failed to setup {self.name}: {e}")
            return False
            
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using the appropriate API with context validation."""
        if not self.is_setup:
            raise RuntimeError(f"Evaluator {self.name} not setup")

        start_time = time.time()
        
        try:
            # STRICT CONTEXT VALIDATION - No truncation allowed
            context_stats = self.validate_context_size(prompt)
            logger.debug(f"Context validation passed for {self.name}: {context_stats}")
            
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
                    else:
                        raise ValueError(f"Unsupported provider: {self.provider}")
                    
                    # Success - return response with context stats
                    metadata = {
                        "model_name": self.model_name,
                        "provider": self.provider,
                        "attempts": attempt + 1
                    }
                    
                    return self._create_response_dict(
                        response_text, 
                        start_time, 
                        metadata=metadata,
                        context_stats=context_stats
                    )

                except OPENAI_NON_RETRYABLE_ERRORS as e:
                if self.provider == "openai":
                    print(f"Attempt {attempt+1}/{max_retries+1}: Non-retryable OpenAI error for {self.name}: {type(e).__name__} - {e}")
                    last_exception = e
                    break 
            except ANTHROPIC_NON_RETRYABLE_ERRORS as e:
                if self.provider == "anthropic":
                    print(f"Attempt {attempt+1}/{max_retries+1}: Non-retryable Anthropic error for {self.name}: {type(e).__name__} - {e}")
                    last_exception = e
                    break
            except GEMINI_NON_RETRYABLE_ERRORS as e:
                if self.provider == "gemini":
                    print(f"Attempt {attempt+1}/{max_retries+1}: Non-retryable Gemini error for {self.name}: {type(e).__name__} - {e}")
                    last_exception = e
                    break
            
            except OPENAI_RETRYABLE_EXCEPTIONS as e:
                if self.provider == "openai":
                    last_exception = e
                    if attempt < max_retries:
                        delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                        print(f"Attempt {attempt+1}/{max_retries+1}: Retryable OpenAI error for {self.name}: {type(e).__name__} - {e}. Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"Attempt {attempt+1}/{max_retries+1}: Max retries reached for OpenAI error: {type(e).__name__} - {e}")
                        break
                else: # Not an OpenAI error, re-raise if not caught by other specific handlers
                    raise
            except ANTHROPIC_RETRYABLE_EXCEPTIONS as e:
                if self.provider == "anthropic":
                    last_exception = e
                    if attempt < max_retries:
                        delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                        print(f"Attempt {attempt+1}/{max_retries+1}: Retryable Anthropic error for {self.name}: {type(e).__name__} - {e}. Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"Attempt {attempt+1}/{max_retries+1}: Max retries reached for Anthropic error: {type(e).__name__} - {e}")
                        break
                else:
                    raise
            except GEMINI_RETRYABLE_EXCEPTIONS as e:
                if self.provider == "gemini":
                    last_exception = e
                    if attempt < max_retries:
                        delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                        print(f"Attempt {attempt+1}/{max_retries+1}: Retryable Gemini error for {self.name}: {type(e).__name__} - {e}. Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"Attempt {attempt+1}/{max_retries+1}: Max retries reached for Gemini error: {type(e).__name__} - {e}")
                        break
                else:
                    raise
            
            except (openai.APIError, anthropic.APIError, google_exceptions.GoogleAPIError) as e: # Catch broader API errors if not caught by specifics
                # These are generally non-retryable unless specified above
                print(f"Attempt {attempt+1}/{max_retries+1}: General API error for {self.name} ({self.provider}): {type(e).__name__} - {e}")
                last_exception = e
                break # Stop retrying for generic API errors not in retryable lists

            except Exception as e:
                print(f"Attempt {attempt+1}/{max_retries+1}: Unexpected error for {self.name} ({self.provider}): {type(e).__name__} - {e}")
                last_exception = e
                break # Stop retrying for unexpected errors

        # If all retries failed or a non-retryable error occurred
        return self._create_response_dict(
            f"Error generating response after {max_retries + 1} attempts: {type(last_exception).__name__} - {str(last_exception)}",
            time.time(), # This will be the time of the last failure, not the initial start
            {"error": True, "error_type": type(last_exception).__name__, "final_attempt_count": attempt + 1}
        )
                
        except ContextLimitExceededError:
            # Re-raise context errors without modification
            raise
        except Exception as e:
            error_msg = f"Generation failed for {self.name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
    async def cleanup(self) -> None:
        """Clean up API connections."""
        if self.client:
            # Close any persistent connections
            if hasattr(self.client, 'close'):
                await self.client.close()
        self.client = None
        self.is_setup = False
    async def _generate_openai(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.9),
            max_tokens=kwargs.get("max_tokens", 4096)
        )
        return response.choices[0].message.content
        
    async def _generate_anthropic(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API."""
        response = await self.client.messages.create(
            model=self.model_name,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.9),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
        
    async def _generate_gemini(self, prompt: str, **kwargs) -> str:
        """Generate response using Gemini API."""
        response = await self.client.generate_content_async(prompt)
        return response.text
        
    async def _test_openai_connection(self) -> None:
        """Test OpenAI API connection."""
        await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1
        )
        
    async def _test_anthropic_connection(self) -> None:
        """Test Anthropic API connection."""
        await self.client.messages.create(
            model=self.model_name,
            max_tokens=1,
            messages=[{"role": "user", "content": "Test"}]
        )
        
    async def _test_gemini_connection(self) -> None:
        """Test Gemini API connection."""
        await self.client.generate_content_async("Test")
