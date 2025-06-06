"""
Comprehensive tests for models/progress.py
These tests cover progress tracking and resume functionality.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime

# Import the models we want to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storybench.models.progress import ProgressTracker


class TestProgressTracker:
    """Test the ProgressTracker class."""
    
    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(results_dir=temp_dir)
            
            assert tracker.results_dir == Path(temp_dir)
            assert tracker.results_dir.exists()
    
    def test_get_result_file_path(self):
        """Test getting result file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(results_dir=temp_dir)
            
            model_name = "gpt-4"
            config_hash = "abc123"
            
            path = tracker.get_result_file_path(model_name, config_hash)
            expected_path = Path(temp_dir) / f"{model_name}_{config_hash}.json"
            
            assert path == expected_path
    
    def test_get_result_file_path_with_special_chars(self):
        """Test getting result file path with special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(results_dir=temp_dir)
            
            model_name = "meta-llama/Llama-2-7b-chat"
            config_hash = "def456"
            
            path = tracker.get_result_file_path(model_name, config_hash)
            expected_name = "meta-llama_Llama-2-7b-chat_def456.json"
            expected_path = Path(temp_dir) / expected_name
            
            assert path == expected_path
            # Check that "/" and spaces are properly replaced
            assert "/" not in path.name
            assert " " not in path.name
    
    def test_save_response_creates_new_file(self):
        """Test saving response creates new file when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(results_dir=temp_dir)
            
            model_name = "gpt-4"
            config_hash = "abc123"
            sequence = "creativity_test"
            run = 1
            prompt_idx = 0
            prompt_name = "creativity_prompt"
            response_data = {
                "response": "This is a creative response",
                "generation_time": 2.5,
                "completed_at": datetime.now().isoformat()
            }
            
            tracker.save_response(
                model_name, config_hash, sequence, run, 
                prompt_idx, prompt_name, response_data
            )
            
            # Check that file was created
            file_path = tracker.get_result_file_path(model_name, config_hash)
            assert file_path.exists()
            
            # Check file contents
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert data["metadata"]["model_name"] == model_name
            assert sequence in data["sequences"]
            assert "run_1" in data["sequences"][sequence]

    
    def test_save_response_appends_to_existing_file(self):
        """Test saving response appends to existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(results_dir=temp_dir)
            
            model_name = "gpt-4"
            config_hash = "abc123"
            
            # Save first response
            tracker.save_response(
                model_name, config_hash, "creativity_test", 1, 0, "prompt1",
                {"response": "First response", "generation_time": 1.0, "completed_at": datetime.now().isoformat()}
            )
            
            # Save second response to same file
            tracker.save_response(
                model_name, config_hash, "creativity_test", 1, 1, "prompt2",
                {"response": "Second response", "generation_time": 1.5, "completed_at": datetime.now().isoformat()}
            )
            
            # Check that both responses are saved
            file_path = tracker.get_result_file_path(model_name, config_hash)
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert len(data["sequences"]["creativity_test"]["run_1"]) == 2
    
    def test_default_results_directory(self):
        """Test that default results directory is 'output'."""
        # Create tracker with default directory
        tracker = ProgressTracker()
        
        assert tracker.results_dir == Path("output")
        
        # Clean up if directory was created
        if Path("output").exists():
            import shutil
            shutil.rmtree("output")


class TestProgressTrackerUtilities:
    """Test utility methods of ProgressTracker."""
    
    def test_file_path_sanitization(self):
        """Test that model names are properly sanitized for file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ProgressTracker(results_dir=temp_dir)
            
            # Test various problematic model names
            test_cases = [
                ("model/with/slashes", "model_with_slashes"),
                ("model with spaces", "model_with_spaces"),
                ("model/with spaces", "model_with_spaces"),
                ("normal-model", "normal-model")
            ]
            
            for input_name, expected_safe_name in test_cases:
                path = tracker.get_result_file_path(input_name, "hash123")
                assert expected_safe_name in path.name
                assert "/" not in path.name
                assert " " not in path.name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
