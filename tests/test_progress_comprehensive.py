"""Comprehensive tests for progress models."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.models.progress import ProgressTracker, EvaluationProgress


class TestProgressTrackerComprehensive:
    """Comprehensive tests for ProgressTracker."""
    
    def test_initialization_defaults(self):
        """Test ProgressTracker initialization with defaults."""
        tracker = ProgressTracker()
        
        assert tracker.current_step == 0
        assert tracker.total_steps == 0
        assert tracker.current_operation == ""
        assert tracker.completion_percentage == 0.0
        assert tracker.estimated_time_remaining is None
        assert len(tracker.completed_steps) == 0
        
    def test_initialization_with_params(self):
        """Test ProgressTracker initialization with parameters."""
        tracker = ProgressTracker(
            current_step=5,
            total_steps=10,
            current_operation="Testing",
            completion_percentage=50.0
        )
        
        assert tracker.current_step == 5
        assert tracker.total_steps == 10
        assert tracker.current_operation == "Testing"
        assert tracker.completion_percentage == 50.0
        
    def test_update_progress_method(self):
        """Test update_progress method."""
        tracker = ProgressTracker(total_steps=10)
        
        tracker.update_progress(5, "Halfway done")
        
        assert tracker.current_step == 5
        assert tracker.current_operation == "Halfway done"
        assert tracker.completion_percentage == 50.0
        
    def test_add_completed_step(self):
        """Test add_completed_step method."""
        tracker = ProgressTracker()
        
        tracker.add_completed_step("Step 1 completed")
        tracker.add_completed_step("Step 2 completed")
        
        assert len(tracker.completed_steps) == 2
        assert "Step 1 completed" in tracker.completed_steps
        assert "Step 2 completed" in tracker.completed_steps
        
    def test_reset_method(self):
        """Test reset method."""
        tracker = ProgressTracker(
            current_step=5,
            total_steps=10,
            current_operation="Testing"
        )
        tracker.add_completed_step("Test step")
        
        tracker.reset()
        
        assert tracker.current_step == 0
        assert tracker.total_steps == 0
        assert tracker.current_operation == ""
        assert tracker.completion_percentage == 0.0
        assert len(tracker.completed_steps) == 0
        
    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation."""
        tracker = ProgressTracker(total_steps=100)
        
        tracker.update_progress(25)
        assert tracker.completion_percentage == 25.0
        
        tracker.update_progress(50)
        assert tracker.completion_percentage == 50.0
        
        tracker.update_progress(100)
        assert tracker.completion_percentage == 100.0
        
    def test_zero_total_steps_division(self):
        """Test handling of zero total steps."""
        tracker = ProgressTracker(total_steps=0)
        
        tracker.update_progress(5)
        
        # Should handle division by zero gracefully
        assert tracker.completion_percentage == 0.0


class TestEvaluationProgressComprehensive:
    """Comprehensive tests for EvaluationProgress."""
    
    def test_initialization_defaults(self):
        """Test EvaluationProgress initialization with defaults."""
        progress = EvaluationProgress()
        
        assert progress.evaluation_id is None
        assert progress.model_name == ""
        assert progress.prompt_name == ""
        assert progress.status == "pending"
        assert progress.current_step == 0
        assert progress.total_steps == 0
        assert progress.completion_percentage == 0.0
        
    def test_initialization_with_params(self):
        """Test EvaluationProgress initialization with parameters."""
        progress = EvaluationProgress(
            evaluation_id=123,
            model_name="test-model",
            prompt_name="test-prompt",
            status="running",
            current_step=2,
            total_steps=5
        )
        
        assert progress.evaluation_id == 123
        assert progress.model_name == "test-model"
        assert progress.prompt_name == "test-prompt"
        assert progress.status == "running"
        assert progress.current_step == 2
        assert progress.total_steps == 5
        assert progress.completion_percentage == 40.0
