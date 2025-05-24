"""API-based LLM evaluator for OpenAI, Anthropic, Google, and other services."""

import asyncio
import time
import random # For jitter
from typing import Dict, Any, Optional, Tuple, Type

import openai
import anthropic
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions # For specific Google exceptions

from .base import BaseEvaluator

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


class APIEvaluator(BaseEvaluator):
    """Evaluator for API-based LLM services."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize API evaluator."""
        super().__init__(name, config)
        self.api_keys = api_keys
        self.provider = config.get("provider", "").lower()
        self.model_name = config.get("model_name", "")
        self.client = None
        
    async def setup(self) -> bool:
        """Setup API client and test connection."""
        try:
            if self.provider == "openai":
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_keys.get("OPENAI_API_KEY")
                )
                await self._test_openai_connection()
                
            elif self.provider == "anthropic":
                self.client = anthropic.AsyncAnthropic(
                    api_key=self.api_keys.get("ANTHROPIC_API_KEY")
                )
                await self._test_anthropic_connection()
                
            elif self.provider == "gemini":
                genai.configure(api_key=self.api_keys.get("GOOGLE_API_KEY"))
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
        """Generate response using the appropriate API."""
        if not self.is_setup:
            raise RuntimeError(f"Evaluator {self.name} not setup")

        max_retries = kwargs.get("max_retries", 3) # Default to 3 if not provided
        base_delay = 1  # seconds
        
        last_exception = None

        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                if self.provider == "openai":
                    response_text = await self._generate_openai(prompt, **kwargs)
                elif self.provider == "anthropic":
                    response_text = await self._generate_anthropic(prompt, **kwargs)
                elif self.provider == "gemini":
                    response_text = await self._generate_gemini(prompt, **kwargs)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
                
                return self._create_response_dict(response_text, start_time)

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
