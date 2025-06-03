"""Enhanced API-based LLM evaluator with unified context management."""

import asyncio
import time
import random
import logging
from typing import Dict, Any, Optional, Tuple, Type

import openai
import anthropic
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .base import BaseEvaluator
from ..unified_context_system import ContextLimitExceededError

logger = logging.getLogger(__name__)

# Define retryable exceptions for each provider
OPENAI_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
)

ANTHROPIC_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    anthropic.RateLimitError,
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)

GEMINI_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    google_exceptions.DeadlineExceeded,
    google_exceptions.ServiceUnavailable,
    google_exceptions.ResourceExhausted,
)

# Non-retryable API errors
OPENAI_NON_RETRYABLE_ERRORS: Tuple[Type[Exception], ...] = (
    openai.AuthenticationError,
    openai.PermissionDeniedError,
    openai.NotFoundError,
    openai.BadRequestError,
    openai.UnprocessableEntityError,
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