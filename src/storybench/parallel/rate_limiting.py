"""
Rate limiting management for parallel API calls across multiple providers.

Handles provider-specific concurrency limits and request rate management
with adaptive backoff and circuit breaker patterns.
"""

import asyncio
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ProviderRateLimit:
    """Rate limiting configuration per provider."""
    max_concurrent: int
    requests_per_minute: int
    burst_capacity: int = 0
    backoff_factor: float = 1.5
    
    def __post_init__(self):
        if self.burst_capacity == 0:
            self.burst_capacity = self.max_concurrent * 2


class RateLimitManager:
    """Manages rate limiting across multiple API providers."""
    
    # Provider-specific rate limits optimized for current 12 models scaling to 50+
    PROVIDER_LIMITS = {
        "anthropic": ProviderRateLimit(max_concurrent=10, requests_per_minute=400),  # Claude models
        "openai": ProviderRateLimit(max_concurrent=12, requests_per_minute=800),     # GPT models  
        "google": ProviderRateLimit(max_concurrent=8, requests_per_minute=600),     # Gemini models
        "deepinfra": ProviderRateLimit(max_concurrent=8, requests_per_minute=300),  # Hosted models
        "local": ProviderRateLimit(max_concurrent=4, requests_per_minute=120)       # Future local models
    }
    
    def __init__(self):
        self.provider_semaphores = {}
        self.request_times = defaultdict(list)
        self.circuit_breakers = defaultdict(bool)  # Track if provider is in circuit breaker mode
        self.error_counts = defaultdict(int)
        self.last_error_reset = defaultdict(lambda: datetime.utcnow())
        
        # Initialize semaphores for each provider
        for provider, limits in self.PROVIDER_LIMITS.items():
            self.provider_semaphores[provider] = asyncio.Semaphore(limits.max_concurrent)
    
    async def acquire(self, provider: str) -> bool:
        """Acquire rate limit permission for provider."""
        if provider not in self.PROVIDER_LIMITS:
            logger.warning(f"Unknown provider {provider}, using anthropic defaults")
            provider = "anthropic"  # Conservative fallback
        
        # Check circuit breaker
        if self.circuit_breakers[provider]:
            if self._should_reset_circuit_breaker(provider):
                self.circuit_breakers[provider] = False
                self.error_counts[provider] = 0
                logger.info(f"Circuit breaker reset for {provider}")
            else:
                await asyncio.sleep(5)  # Wait before retry
                return False
        
        # Wait for semaphore (concurrent requests limit)
        await self.provider_semaphores[provider].acquire()
        
        # Check per-minute rate limit
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.request_times[provider] = [
            t for t in self.request_times[provider] if t > minute_ago
        ]
        
        # Check if we're under the per-minute limit
        current_requests = len(self.request_times[provider])
        limit = self.PROVIDER_LIMITS[provider].requests_per_minute
        
        if current_requests >= limit:
            # Need to wait until we can make another request
            if self.request_times[provider]:
                oldest_request = min(self.request_times[provider])
                wait_until = oldest_request + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.debug(f"Rate limit hit for {provider}, waiting {wait_seconds:.1f}s")
                    await asyncio.sleep(wait_seconds)
        
        # Record this request
        self.request_times[provider].append(now)
        return True
    
    def release(self, provider: str):
        """Release rate limit permission for provider."""
        if provider in self.provider_semaphores:
            self.provider_semaphores[provider].release()
    
    def record_error(self, provider: str):
        """Record an API error for circuit breaker logic."""
        self.error_counts[provider] += 1
        
        # Trip circuit breaker after 5 consecutive errors
        if self.error_counts[provider] >= 5:
            self.circuit_breakers[provider] = True
            self.last_error_reset[provider] = datetime.utcnow()
            logger.warning(f"Circuit breaker tripped for {provider} after {self.error_counts[provider]} errors")
    
    def record_success(self, provider: str):
        """Record a successful API call."""
        if self.error_counts[provider] > 0:
            self.error_counts[provider] = max(0, self.error_counts[provider] - 1)
    
    def _should_reset_circuit_breaker(self, provider: str) -> bool:
        """Check if circuit breaker should be reset."""
        if not self.circuit_breakers[provider]:
            return False
        
        # Reset after 30 seconds
        reset_time = self.last_error_reset[provider] + timedelta(seconds=30)
        return datetime.utcnow() > reset_time
    
    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """Get current rate limit stats for a provider."""
        if provider not in self.PROVIDER_LIMITS:
            return {"error": "Unknown provider"}
        
        limits = self.PROVIDER_LIMITS[provider]
        current_concurrent = limits.max_concurrent - self.provider_semaphores[provider]._value
        minute_requests = len([
            t for t in self.request_times[provider] 
            if t > datetime.utcnow() - timedelta(minutes=1)
        ])
        
        return {
            "provider": provider,
            "max_concurrent": limits.max_concurrent,
            "current_concurrent": current_concurrent,
            "requests_per_minute_limit": limits.requests_per_minute,
            "requests_this_minute": minute_requests,
            "utilization_percent": (current_concurrent / limits.max_concurrent) * 100,
            "circuit_breaker_active": self.circuit_breakers[provider],
            "error_count": self.error_counts[provider]
        }
    
    def get_all_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all providers."""
        return {
            provider: self.get_provider_stats(provider) 
            for provider in self.PROVIDER_LIMITS.keys()
        }
