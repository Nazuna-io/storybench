"""Enhanced error handling utilities for API validation."""

import asyncio
import functools
from typing import Any, Callable, TypeVar, Union

T = TypeVar('T')


def timeout_after(seconds: float):
    """Decorator to add timeout to async functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator


def safe_api_call(error_message: str = "API call failed"):
    """Decorator to safely handle API calls with error wrapping."""
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log the actual error but return a clean message
                print(f"API Error in {func.__name__}: {str(e)}")
                raise Exception(f"{error_message}: {str(e)}")
        return wrapper
    return decorator


class APIValidationError(Exception):
    """Custom exception for API validation failures."""
    
    def __init__(self, provider: str, message: str, original_error: Exception = None):
        self.provider = provider
        self.message = message
        self.original_error = original_error
        super().__init__(f"{provider}: {message}")


def normalize_api_error(provider: str, error: Exception) -> str:
    """Normalize API errors to user-friendly messages."""
    error_str = str(error).lower()
    
    # Common error patterns across providers
    if "authentication" in error_str or "unauthorized" in error_str or "invalid api key" in error_str:
        return "Invalid API key or authentication failed"
    elif "rate limit" in error_str or "quota" in error_str:
        return "Rate limit exceeded - please try again later"
    elif "timeout" in error_str or "deadline" in error_str:
        return "Request timed out - API may be slow or unavailable"
    elif "not found" in error_str or "model not found" in error_str:
        return "Model not found or not accessible with current API key"
    elif "permission" in error_str or "forbidden" in error_str:
        return "Permission denied - check API key permissions"
    elif "connection" in error_str or "network" in error_str:
        return "Network connection failed"
    elif "service unavailable" in error_str or "internal server" in error_str:
        return "API service temporarily unavailable"
    else:
        return f"API error: {str(error)}"
