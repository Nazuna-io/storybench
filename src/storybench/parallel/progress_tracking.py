"""
Progress tracking system for parallel evaluations.

Provides real-time monitoring and aggregated statistics for concurrent
sequence workers with performance metrics and ETA calculations.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ParallelEvaluationProgress:
    """Aggregated progress tracking for parallel evaluation."""
    total_workers: int = 0
    active_workers: int = 0
    completed_workers: int = 0
    failed_workers: int = 0
    total_prompts: int = 0
    completed_prompts: int = 0
    start_time: Optional[datetime] = None
    
    # Performance tracking
    provider_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    worker_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        if self.total_prompts == 0:
            return 0.0
        return (self.completed_prompts / self.total_prompts) * 100
    
    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate time remaining based on current progress rate."""
        if not self.start_time or self.completed_prompts == 0:
            return None
            
        elapsed = datetime.utcnow() - self.start_time
        prompts_per_second = self.completed_prompts / elapsed.total_seconds()
        remaining_prompts = self.total_prompts - self.completed_prompts
        
        if prompts_per_second > 0:
            remaining_seconds = remaining_prompts / prompts_per_second
            return timedelta(seconds=remaining_seconds)
        return None
    
    @property
    def current_throughput(self) -> float:
        """Calculate current prompts per minute."""
        if not self.start_time:
            return 0.0
        
        elapsed = datetime.utcnow() - self.start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        
        if elapsed_minutes > 0:
            return self.completed_prompts / elapsed_minutes
        return 0.0
    
    def update_worker_count(self, active: int, completed: int, failed: int):
        """Update worker counts."""
        self.active_workers = active
        self.completed_workers = completed
        self.failed_workers = failed
        self.total_workers = active + completed + failed
    
    def add_completed_prompts(self, count: int):
        """Add completed prompts (thread-safe increment)."""
        self.completed_prompts += count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_workers": self.total_workers,
            "active_workers": self.active_workers,
            "completed_workers": self.completed_workers,
            "failed_workers": self.failed_workers,
            "total_prompts": self.total_prompts,
            "completed_prompts": self.completed_prompts,
            "completion_percentage": self.completion_percentage,
            "current_throughput_per_minute": self.current_throughput,
            "estimated_time_remaining_seconds": (
                self.estimated_time_remaining.total_seconds() 
                if self.estimated_time_remaining else None
            ),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "provider_stats": self.provider_stats,
            "worker_performance": self.worker_performance
        }


class ProgressReporter:
    """Real-time progress reporting for parallel evaluations."""
    
    def __init__(self, progress: ParallelEvaluationProgress, 
                 log_interval: int = 30,
                 detailed_logging: bool = False):
        self.progress = progress
        self.log_interval = log_interval  # seconds
        self.detailed_logging = detailed_logging
        self.last_log_time = None
        self.last_completed_count = 0
    
    def should_log_progress(self) -> bool:
        """Check if enough time has passed to log progress."""
        now = datetime.utcnow()
        
        if self.last_log_time is None:
            self.last_log_time = now
            return True
        
        return (now - self.last_log_time).total_seconds() >= self.log_interval
    
    def log_progress(self, force: bool = False):
        """Log current progress if interval has passed."""
        if not force and not self.should_log_progress():
            return
        
        now = datetime.utcnow()
        
        # Calculate recent throughput
        recent_completed = self.progress.completed_prompts - self.last_completed_count
        time_diff = (now - self.last_log_time).total_seconds() if self.last_log_time else 1
        recent_throughput = (recent_completed / time_diff) * 60  # per minute
        
        # Basic progress log
        logger.info(
            f"Parallel Evaluation Progress: "
            f"{self.progress.completed_prompts}/{self.progress.total_prompts} prompts "
            f"({self.progress.completion_percentage:.1f}%) | "
            f"Workers: {self.progress.active_workers} active, "
            f"{self.progress.completed_workers} completed, "
            f"{self.progress.failed_workers} failed | "
            f"Throughput: {self.progress.current_throughput:.1f} prompts/min "
            f"(recent: {recent_throughput:.1f})"
        )
        
        # ETA if available
        if self.progress.estimated_time_remaining:
            eta_minutes = self.progress.estimated_time_remaining.total_seconds() / 60
            logger.info(f"Estimated time remaining: {eta_minutes:.1f} minutes")
        
        # Detailed provider stats if enabled
        if self.detailed_logging and self.progress.provider_stats:
            for provider, stats in self.progress.provider_stats.items():
                if stats.get("current_concurrent", 0) > 0:
                    logger.debug(
                        f"Provider {provider}: "
                        f"{stats['current_concurrent']}/{stats['max_concurrent']} concurrent, "
                        f"{stats['requests_this_minute']}/{stats['requests_per_minute_limit']} requests/min, "
                        f"{stats['utilization_percent']:.1f}% utilized"
                    )
        
        # Update tracking variables
        self.last_log_time = now
        self.last_completed_count = self.progress.completed_prompts
    
    def log_final_summary(self, results: Dict[str, Any]):
        """Log final evaluation summary."""
        duration_minutes = results.get("total_duration", 0) / 60
        
        logger.info("=" * 60)
        logger.info("PARALLEL EVALUATION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total Duration: {duration_minutes:.1f} minutes")
        logger.info(f"Total Prompts: {self.progress.total_prompts}")
        logger.info(f"Completed Prompts: {self.progress.completed_prompts}")
        logger.info(f"Average Throughput: {self.progress.current_throughput:.1f} prompts/min")
        logger.info(f"Workers: {results['successful_workers']}/{results['total_workers']} successful")
        
        # Provider performance summary
        if results.get("provider_stats"):
            logger.info("\nProvider Performance:")
            for provider, stats in results["provider_stats"].items():
                logger.info(f"  {provider}: {stats.get('utilization_percent', 0):.1f}% average utilization")
        
        logger.info("=" * 60)
