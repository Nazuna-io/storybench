"""Database query performance monitoring utilities."""

import time
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from functools import wraps

logger = logging.getLogger(__name__)

class QueryPerformanceMonitor:
    """Monitor and log database query performance."""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # Log queries taking over 1 second
        
    @asynccontextmanager
    async def monitor_query(self, query_name: str, details: Optional[Dict[str, Any]] = None):
        """Context manager to monitor query execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            # Update statistics
            if query_name not in self.query_stats:
                self.query_stats[query_name] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "min_time": float('inf')
                }
            
            stats = self.query_stats[query_name]
            stats["count"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["max_time"] = max(stats["max_time"], execution_time)
            stats["min_time"] = min(stats["min_time"], execution_time)
            
            # Log if slow
            if execution_time > self.slow_query_threshold:
                details_str = f" | Details: {details}" if details else ""
                logger.warning(f"Slow query detected: {query_name} took {execution_time:.3f}s{details_str}")
            else:
                logger.debug(f"Query performance: {query_name} took {execution_time:.3f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of query performance statistics."""
        return {
            "query_stats": dict(self.query_stats),
            "total_queries": sum(stats["count"] for stats in self.query_stats.values()),
            "total_time": sum(stats["total_time"] for stats in self.query_stats.values()),
            "slowest_queries": sorted(
                [(name, stats["max_time"]) for name, stats in self.query_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.query_stats.clear()

# Global performance monitor instance
performance_monitor = QueryPerformanceMonitor()

def monitor_query_performance(query_name: str, details: Optional[Dict[str, Any]] = None):
    """Decorator to monitor query performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with performance_monitor.monitor_query(query_name, details):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
