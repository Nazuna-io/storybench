"""Comprehensive ProgressTracker tests for coverage boost."""

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.models.progress import ProgressTracker


class TestProgressTrackerComprehensive:
    """Comprehensive ProgressTracker tests."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
            
    @pytest.fixture
    def progress_tracker(self, temp_dir):
        """ProgressTracker fixture with temp directory."""
        return ProgressTracker(results_dir=temp_dir)
        
    def test_progress_tracker_initialization_default(self):
        """Test ProgressTracker initialization with default directory."""
        tracker = ProgressTracker()
        
        assert tracker.results_dir.name == "output"
        assert tracker.results_dir.exists()
        
    def test_progress_tracker_initialization_custom_dir(self, temp_dir):
        """Test ProgressTracker with custom directory."""
        tracker = ProgressTracker(results_dir=temp_dir)
        
        assert str(tracker.results_dir) == temp_dir
        assert tracker.results_dir.exists()
        
    def test_get_result_file_path(self, progress_tracker):
        """Test get_result_file_path method."""
        model_name = "test/model-name"
        config_hash = "abc123"
        
        file_path = progress_tracker.get_result_file_path(model_name, config_hash)
        
        assert file_path.name == "test_model-name_abc123.json"
        assert file_path.parent == progress_tracker.results_dir
        
    def test_get_result_file_path_special_characters(self, progress_tracker):
        """Test file path with special characters."""
        model_name = "test model/with spaces"
        config_hash = "def456"
        
        file_path = progress_tracker.get_result_file_path(model_name, config_hash)
        
        assert file_path.name == "test_model_with_spaces_def456.json"
        
    def test_save_response_new_file(self, progress_tracker):
        """Test saving response to new file."""
        model_name = "test-model"
        config_hash = "hash123"
        sequence = "test_sequence"
        run = 1
        prompt_idx = 0
        prompt_name = "test_prompt"
        response_data = {
            "response": "Test response",
            "tokens": 50,
            "time": 1.5
        }
        
        progress_tracker.save_response(
            model_name, config_hash, sequence, run, prompt_idx, 
            prompt_name, response_data
        )
        
        file_path = progress_tracker.get_result_file_path(model_name, config_hash)
        assert file_path.exists()
        
        # Verify file content
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        assert sequence in data
        assert run in data[sequence]
        assert prompt_idx in data[sequence][run]
        assert data[sequence][run][prompt_idx]["prompt_name"] == prompt_name
        assert data[sequence][run][prompt_idx]["response_data"] == response_data
        
    def test_save_response_existing_file(self, progress_tracker):
        """Test saving response to existing file."""
        model_name = "test-model"
        config_hash = "hash123"
        
        # Save first response
        progress_tracker.save_response(
            model_name, config_hash, "seq1", 1, 0, "prompt1",
            {"response": "First response"}
        )
        
        # Save second response
        progress_tracker.save_response(
            model_name, config_hash, "seq1", 1, 1, "prompt2", 
            {"response": "Second response"}
        )
        
        file_path = progress_tracker.get_result_file_path(model_name, config_hash)
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        assert len(data["seq1"][1]) == 2
        assert data["seq1"][1][0]["response_data"]["response"] == "First response"
        assert data["seq1"][1][1]["response_data"]["response"] == "Second response"
        
    def test_has_result_file(self, progress_tracker):
        """Test has_result method."""
        model_name = "test-model"
        config_hash = "hash123"
        
        # Should not exist initially
        assert not progress_tracker.has_result(model_name, config_hash, "seq1", 1, 0)
        
        # Save a response
        progress_tracker.save_response(
            model_name, config_hash, "seq1", 1, 0, "prompt1",
            {"response": "Test response"}
        )
        
        # Should exist now
        assert progress_tracker.has_result(model_name, config_hash, "seq1", 1, 0)
        
        # Different prompt should not exist
        assert not progress_tracker.has_result(model_name, config_hash, "seq1", 1, 1)
        
    def test_get_resume_info(self, progress_tracker):
        """Test get_resume_info method."""
        model_name = "test-model"
        config_hash = "hash123"
        
        # Save multiple responses
        for i in range(3):
            progress_tracker.save_response(
                model_name, config_hash, "test_seq", 1, i, f"prompt_{i}",
                {"response": f"Response {i}"}
            )
            
        resume_info = progress_tracker.get_resume_info(model_name, config_hash)
        
        assert "test_seq" in resume_info
        assert 1 in resume_info["test_seq"]
        assert len(resume_info["test_seq"][1]) == 3
        
    def test_get_resume_info_nonexistent(self, progress_tracker):
        """Test get_resume_info for nonexistent file."""
        resume_info = progress_tracker.get_resume_info("nonexistent", "hash")
        
        assert resume_info == {}
        
    def test_load_response_data(self, progress_tracker):
        """Test load_response_data method."""
        model_name = "test-model"
        config_hash = "hash123"
        response_data = {
            "response": "Test response",
            "tokens": 100,
            "metadata": {"key": "value"}
        }
        
        # Save response
        progress_tracker.save_response(
            model_name, config_hash, "seq1", 1, 0, "prompt1", response_data
        )
        
        # Load response
        loaded_data = progress_tracker.load_response_data(
            model_name, config_hash, "seq1", 1, 0
        )
        
        assert loaded_data == response_data
        
    def test_load_response_data_nonexistent(self, progress_tracker):
        """Test loading nonexistent response data."""
        loaded_data = progress_tracker.load_response_data(
            "nonexistent", "hash", "seq", 1, 0
        )
        
        assert loaded_data is None
