"""Unified API retry logic with circuit breaker pattern."""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional, Callable, Type, Tuple, List
from dataclasses import dataclass
from enum import Enum

# Import provider-specific exceptions
import openai
import anthropic
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter_range: float = 1.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 60.0
    circuit_half_open_max_calls: int = 3

# Provider-specific exception mappings
PROVIDER_EXCEPTIONS = {
    "openai": {
        "retryable": (
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.InternalServerError,
        ),
        "non_retryable": (
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            openai.NotFoundError,
            openai.BadRequestError,
            openai.UnprocessableEntityError,
        )
    },
    "anthropic": {
        "retryable": (
            anthropic.RateLimitError,
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.InternalServerError,
        ),
        "non_retryable": (
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
            anthropic.NotFoundError,
            anthropic.BadRequestError,
        )
    },
    "gemini": {
        "retryable": (
            google_exceptions.DeadlineExceeded,
            google_exceptions.ServiceUnavailable,
            google_exceptions.ResourceExhausted,
        ),
        "non_retryable": (
            google_exceptions.PermissionDenied,
            google_exceptions.NotFound,
            google_exceptions.InvalidArgument,
            google_exceptions.FailedPrecondition,
            google_exceptions.Unauthenticated,
        )
    },
    "deepinfra": {
        # DeepInfra uses OpenAI-compatible API
        "retryable": (
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.InternalServerError,
        ),
        "non_retryable": (
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            openai.NotFoundError,
            openai.BadRequestError,
            openai.UnprocessableEntityError,
        )
    }
}

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    
    def __init__(self, provider: str, config: RetryConfig):
        self.provider = provider
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.config.circuit_recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker for {self.provider} moving to HALF_OPEN state")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited calls to test recovery
            return self.half_open_calls < self.config.circuit_half_open_max_calls
        return False
    
    def record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.circuit_half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker for {self.provider} recovered to CLOSED state")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker for {self.provider} failed during HALF_OPEN, returning to OPEN state")
        elif (self.state == CircuitState.CLOSED and 
              self.failure_count >= self.config.circuit_failure_threshold):
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker for {self.provider} OPENED due to {self.failure_count} failures")

class APIRetryHandler:
    """Unified retry handler for all API providers with circuit breaker."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_stats: Dict[str, Dict[str, int]] = {}
        
    def _get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider."""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker(provider, self.config)
        return self.circuit_breakers[provider]
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = min(
            self.config.base_delay * (self.config.backoff_multiplier ** attempt),
            self.config.max_delay
        )
        jitter = random.uniform(0, self.config.jitter_range)
        return delay + jitter
    
    def _is_retryable_error(self, provider: str, exception: Exception) -> bool:
        """Check if exception is retryable for the given provider."""
        if provider not in PROVIDER_EXCEPTIONS:
            return False
        
        retryable_exceptions = PROVIDER_EXCEPTIONS[provider]["retryable"]
        return isinstance(exception, retryable_exceptions)
    
    def _is_non_retryable_error(self, provider: str, exception: Exception) -> bool:
        """Check if exception is non-retryable for the given provider."""
        if provider not in PROVIDER_EXCEPTIONS:
            return False
        
        non_retryable_exceptions = PROVIDER_EXCEPTIONS[provider]["non_retryable"]
        return isinstance(exception, non_retryable_exceptions)
    
    def _update_stats(self, provider: str, event: str):
        """Update retry statistics."""
        if provider not in self.retry_stats:
            self.retry_stats[provider] = {
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "circuit_breaks": 0,
                "non_retryable_errors": 0
            }
        self.retry_stats[provider][event] += 1

    async def execute_with_retry(self, 
                                provider: str,
                                operation: Callable,
                                operation_name: str = "API call",
                                **kwargs) -> Any:
        """Execute operation with unified retry logic and circuit breaker."""
        circuit_breaker = self._get_circuit_breaker(provider)
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            self._update_stats(provider, "circuit_breaks")
            raise RuntimeError(f"Circuit breaker OPEN for {provider} - operation blocked")
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            self._update_stats(provider, "total_attempts")
            
            try:
                result = await operation(**kwargs)
                
                # Success - update stats and circuit breaker
                self._update_stats(provider, "successful_attempts")
                circuit_breaker.record_success()
                
                if attempt > 0:
                    logger.info(f"✅ {operation_name} succeeded for {provider} after {attempt + 1} attempts")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if it's a non-retryable error
                if self._is_non_retryable_error(provider, e):
                    self._update_stats(provider, "non_retryable_errors")
                    circuit_breaker.record_failure()
                    logger.error(f"❌ Non-retryable {provider} error in {operation_name}: {type(e).__name__} - {e}")
                    raise e
                
                # Check if it's a retryable error
                if self._is_retryable_error(provider, e):
                    circuit_breaker.record_failure()
                    
                    if attempt < self.config.max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(f"⚠️  Retryable {provider} error in {operation_name}: {type(e).__name__} - {e}. "
                                     f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Max retries ({self.config.max_retries}) reached for {provider} {operation_name}: {type(e).__name__} - {e}")
                        break
                else:
                    # Unknown error type - don't retry but don't break circuit
                    logger.error(f"❌ Unknown error type for {provider} {operation_name}: {type(e).__name__} - {e}")
                    raise e
        
        # All retries exhausted
        self._update_stats(provider, "failed_attempts")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Operation failed after {self.config.max_retries + 1} attempts")
    
    def get_retry_stats(self) -> Dict[str, Dict[str, int]]:
        """Get retry statistics for all providers."""
        return dict(self.retry_stats)
    
    def reset_circuit_breaker(self, provider: str):
        """Reset circuit breaker for a provider (for testing/manual recovery)."""
        if provider in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[provider]
            circuit_breaker.state = CircuitState.CLOSED
            circuit_breaker.failure_count = 0
            logger.info(f"Circuit breaker for {provider} manually reset to CLOSED state")

# Global retry handler instance
retry_handler = APIRetryHandler()
