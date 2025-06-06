"""Comprehensive progress models tests for coverage boost."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.models.progress import ProgressTracker


class TestProgressTrackerComprehensive:
    """Comprehensive ProgressTracker tests."""
    
    def test_progress_tracker_initialization_defaults(self):
        """Test ProgressTracker initialization with defaults."""
        tracker = ProgressTracker()
        
        assert tracker.current_step == 0
        assert tracker.total_steps == 0
        assert tracker.current_operation == ""
        assert tracker.completion_percentage == 0.0
        assert tracker.estimated_time_remaining is None
        assert len(tracker.completed_steps) == 0
        
    def test_progress_tracker_initialization_with_values(self):
        """Test ProgressTracker with initial values."""
        tracker = ProgressTracker(
            current_step=5,
            total_steps=10,
            current_operation="Processing",
            completion_percentage=50.0
        )
        
        assert tracker.current_step == 5
        assert tracker.total_steps == 10
        assert tracker.current_operation == "Processing"
        assert tracker.completion_percentage == 50.0
        
    def test_update_progress_basic(self):
        """Test basic update_progress method."""
        tracker = ProgressTracker(total_steps=10)
        
        tracker.update_progress(3, "Step 3 completed")
        
        assert tracker.current_step == 3
        assert tracker.current_operation == "Step 3 completed"
        assert tracker.completion_percentage == 30.0
        
    def test_update_progress_percentage_calculation(self):
        """Test percentage calculation in update_progress."""
        tracker = ProgressTracker(total_steps=100)
        
        tracker.update_progress(25)
        assert tracker.completion_percentage == 25.0
        
        tracker.update_progress(75)
        assert tracker.completion_percentage == 75.0
        
        tracker.update_progress(100)
        assert tracker.completion_percentage == 100.0
        
    def test_update_progress_zero_total_steps(self):
        """Test update_progress with zero total steps."""
        tracker = ProgressTracker(total_steps=0)
        
        tracker.update_progress(5)
        
        # Should handle division by zero gracefully
        assert tracker.completion_percentage == 0.0
        assert tracker.current_step == 5
        
    def test_add_completed_step(self):
        """Test add_completed_step method."""
        tracker = ProgressTracker()
        
        tracker.add_completed_step("Step 1: Initialization")
        tracker.add_completed_step("Step 2: Data loading")
        tracker.add_completed_step("Step 3: Processing")
        
        assert len(tracker.completed_steps) == 3
        assert "Step 1: Initialization" in tracker.completed_steps
        assert "Step 2: Data loading" in tracker.completed_steps
        assert "Step 3: Processing" in tracker.completed_steps
        
    def test_reset_method(self):
        """Test reset method."""
        tracker = ProgressTracker(
            current_step=8,
            total_steps=10,
            current_operation="Almost done"
        )
        tracker.add_completed_step("Test step")
        tracker.add_completed_step("Another step")
        
        tracker.reset()
        
        assert tracker.current_step == 0
        assert tracker.total_steps == 0
        assert tracker.current_operation == ""
        assert tracker.completion_percentage == 0.0
        assert tracker.estimated_time_remaining is None
        assert len(tracker.completed_steps) == 0
        
    def test_progress_with_estimated_time(self):
        """Test progress with estimated time remaining."""
        tracker = ProgressTracker(
            current_step=3,
            total_steps=10,
            estimated_time_remaining=14.5
        )
        
        assert tracker.estimated_time_remaining == 14.5
        
    def test_completion_percentage_edge_cases(self):
        """Test completion percentage edge cases."""
        # Test with current step greater than total
        tracker = ProgressTracker(total_steps=10)
        tracker.update_progress(15)
        
        # Should handle gracefully (implementation dependent)
        assert tracker.current_step == 15
        
    def test_multiple_operations_sequence(self):
        """Test sequence of operations."""
        tracker = ProgressTracker(total_steps=5)
        
        operations = [
            "Loading configuration",
            "Connecting to database", 
            "Processing data",
            "Generating report",
            "Cleanup"
        ]
        
        for i, operation in enumerate(operations, 1):
            tracker.update_progress(i, operation)
            tracker.add_completed_step(operation)
            
        assert tracker.current_step == 5
        assert tracker.completion_percentage == 100.0
        assert len(tracker.completed_steps) == 5
        assert tracker.current_operation == "Cleanup"
        
    def test_progress_tracker_string_representation(self):
        """Test string representation of progress tracker."""
        tracker = ProgressTracker(
            current_step=3,
            total_steps=10,
            current_operation="Processing data"
        )
        
        # Should be able to convert to string without error
        str_repr = str(tracker)
        assert isinstance(str_repr, str)
        
    def test_progress_tracker_with_float_percentage(self):
        """Test progress tracker with precise percentage calculations."""
        tracker = ProgressTracker(total_steps=3)
        
        tracker.update_progress(1)
        assert abs(tracker.completion_percentage - 33.333333333333336) < 0.001
        
        tracker.update_progress(2)
        assert abs(tracker.completion_percentage - 66.66666666666667) < 0.001
        
    def test_empty_operation_handling(self):
        """Test handling of empty operations."""
        tracker = ProgressTracker(total_steps=5)
        
        tracker.update_progress(2, "")
        assert tracker.current_operation == ""
        
        tracker.update_progress(3)  # No operation provided
        assert tracker.current_step == 3
