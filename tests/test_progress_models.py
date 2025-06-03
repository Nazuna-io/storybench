"""Test progress tracking models."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.storybench.models.progress import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Create a ProgressTracker instance."""
        return ProgressTracker(results_dir=temp_dir)
    
    def test_initialization(self, temp_dir):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(results_dir=temp_dir)
        assert tracker.results_dir == Path(temp_dir)
        assert tracker.results_dir.exists()
        
    def test_initialization_creates_directory(self):
        """Test that initialization creates results directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "new_results"
            tracker = ProgressTracker(results_dir=str(subdir))
            assert subdir.exists()
    
    def test_get_result_file_path(self, tracker):
        """Test result file path generation."""
        path = tracker.get_result_file_path("gpt-4", "abc123")
        assert path.name == "gpt-4_abc123.json"
        assert path.parent == tracker.results_dir
        
    def test_get_result_file_path_safe_name(self, tracker):
        """Test result file path with unsafe characters."""
        path = tracker.get_result_file_path("org/model name", "abc123")
        assert path.name == "org_model_name_abc123.json"
    def test_create_empty_result_structure(self, tracker):
        """Test empty result structure creation."""
        with patch('src.storybench.models.progress.datetime') as mock_dt:
            mock_dt.utcnow.return_value.isoformat.return_value = "2024-01-01T12:00:00"
            structure = tracker._create_empty_result_structure("test-model")
            assert structure["metadata"]["model_name"] == "test-model"
            assert structure["metadata"]["config_version"] == 1
            assert structure["metadata"]["timestamp"] == "2024-01-01T12:00:00Z"
            assert structure["metadata"]["last_updated"] == "2024-01-01T12:00:00Z"
            assert structure["metadata"]["global_settings"] == {}
            assert structure["sequences"] == {}
            assert structure["evaluation_scores"] == {}
            assert structure["status"] == "in_progress"
    
    def test_save_response_new_file(self, tracker):
        """Test saving response to new file."""
        response_data = {
            "prompt_text": "Test prompt",
            "response": "Test response",
            "generation_time": 1.5,
            "completed_at": "2024-01-01T12:00:00Z"
        }
        
        with patch('src.storybench.models.progress.datetime') as mock_dt:
            mock_dt.utcnow.return_value.isoformat.return_value = "2024-01-01T12:30:00"
            tracker.save_response("gpt-4", "abc123", "seq1", 1, 0, "prompt1", response_data)
        
        file_path = tracker.get_result_file_path("gpt-4", "abc123")
        assert file_path.exists()
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert data["metadata"]["model_name"] == "gpt-4"
        assert data["metadata"]["last_updated"] == "2024-01-01T12:30:00Z"
        assert "seq1" in data["sequences"]
        assert "run_1" in data["sequences"]["seq1"]
        assert len(data["sequences"]["seq1"]["run_1"]) == 1
        
        response = data["sequences"]["seq1"]["run_1"][0]
        assert response["prompt_name"] == "prompt1"
        assert response["prompt_text"] == "Test prompt"
        assert response["response"] == "Test response"
        assert response["generation_time"] == 1.5
        assert response["completed_at"] == "2024-01-01T12:00:00Z"
    
    def test_save_response_existing_file(self, tracker):
        """Test saving response to existing file."""
        response_data_1 = {
            "prompt_text": "Test prompt 1",
            "response": "Test response 1",
            "generation_time": 1.0,
            "completed_at": "2024-01-01T12:00:00Z"
        }
        tracker.save_response("gpt-4", "abc123", "seq1", 1, 0, "prompt1", response_data_1)
        
        response_data_2 = {
            "prompt_text": "Test prompt 2",
            "response": "Test response 2",
            "generation_time": 2.0,
            "completed_at": "2024-01-01T12:01:00Z"
        }
        tracker.save_response("gpt-4", "abc123", "seq1", 1, 1, "prompt2", response_data_2)
        file_path = tracker.get_result_file_path("gpt-4", "abc123")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        responses = data["sequences"]["seq1"]["run_1"]
        assert len(responses) == 2
        assert responses[0]["prompt_name"] == "prompt1"
        assert responses[1]["prompt_name"] == "prompt2"
    
    def test_task_completed(self, tracker):
        """Test _task_completed method."""
        data = {"sequences": {}}
        assert not tracker._task_completed(data, "seq1", 1, 0)
        
        data = {"sequences": {"seq1": {}}}
        assert not tracker._task_completed(data, "seq1", 1, 0)
        
        data = {"sequences": {"seq1": {"run_1": []}}}
        assert not tracker._task_completed(data, "seq1", 1, 0)
        
        data = {"sequences": {"seq1": {"run_1": [None]}}}
        assert not tracker._task_completed(data, "seq1", 1, 0)
        
        data = {"sequences": {"seq1": {"run_1": [{"response": "test"}]}}}
        assert tracker._task_completed(data, "seq1", 1, 0)
    
    def test_is_complete_empty_file(self, tracker):
        """Test is_complete with non-existent file."""
        assert not tracker.is_complete("gpt-4", "abc123", ["seq1"], 1, {"seq1": 2})
    
    def test_is_complete_incomplete(self, tracker):
        """Test is_complete with incomplete data."""
        response_data = {
            "prompt_text": "Test",
            "response": "Test",
            "generation_time": 1.0,
            "completed_at": "2024-01-01T12:00:00Z"
        }
        tracker.save_response("gpt-4", "abc123", "seq1", 1, 0, "prompt1", response_data)
        
        assert not tracker.is_complete("gpt-4", "abc123", ["seq1"], 1, {"seq1": 2})
    
    def test_get_next_task_new_file(self, tracker):
        """Test get_next_task with non-existent file."""
        task = tracker.get_next_task("gpt-4", "abc123", ["seq1", "seq2"], 2, {"seq1": 2, "seq2": 1})
        assert task == ("seq1", 1, 0)
    
    def test_get_next_task_all_complete(self, tracker):
        """Test get_next_task when all tasks are complete."""
        response_data = {
            "prompt_text": "Test",
            "response": "Test",
            "generation_time": 1.0,
            "completed_at": "2024-01-01T12:00:00Z"
        }
        
        tracker.save_response("gpt-4", "abc123", "seq1", 1, 0, "prompt1", response_data)
        task = tracker.get_next_task("gpt-4", "abc123", ["seq1"], 1, {"seq1": 1})
        assert task is None
    
    def test_default_results_dir(self):
        """Test default results directory."""
        tracker = ProgressTracker()
        assert tracker.results_dir == Path("output")
