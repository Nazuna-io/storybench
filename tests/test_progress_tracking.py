"""Test progress tracking and resume functionality."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch
from src.storybench.models.progress import ProgressTracker
from src.storybench.models.config import Config, GlobalSettings
from src.storybench.evaluators.api_evaluator import APIEvaluator


class MockAPIEvaluator:
    """Mock evaluator for testing."""
    
    def __init__(self, name: str, response_prefix: str = "Mock response"):
        self.name = name
        self.is_setup = False
        self.response_prefix = response_prefix
        
    async def setup(self):
        self.is_setup = True
        return True
        
    async def cleanup(self):
        pass
        
    async def generate_response(self, prompt: str, **kwargs):
        """Generate a mock response."""
        import time
        from datetime import datetime
        
        start_time = time.time()
        response_text = f"{self.response_prefix} for: {prompt[:50]}..."
        
        return {
            "response": response_text,
            "generation_time": 0.1,  # Fast for testing
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "metadata": {}
        }


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Config("dummy_path")
    config.global_settings = GlobalSettings(
        temperature=0.9,
        max_tokens=4096,
        num_runs=2,  # Smaller for testing
        vram_limit_percent=80
    )
    
    # Simple test prompts
    config.prompts = {
        "TestSequence1": [
            {"name": "Prompt1", "text": "Test prompt 1"},
            {"name": "Prompt2", "text": "Test prompt 2"}
        ],
        "TestSequence2": [
            {"name": "Prompt3", "text": "Test prompt 3"}
        ]
    }
    
    return config


def test_progress_tracker_empty(temp_dir):
    """Test progress tracker with no existing data."""
    tracker = ProgressTracker(temp_dir)
    
    sequences = ["TestSequence1", "TestSequence2"]
    prompts_per_sequence = {"TestSequence1": 2, "TestSequence2": 1}
    
    # Should not be complete
    assert not tracker.is_complete("TestModel", "testhash", sequences, 2, prompts_per_sequence)
    
    # Should get first task
    next_task = tracker.get_next_task("TestModel", "testhash", sequences, 2, prompts_per_sequence)
    assert next_task == ("TestSequence1", 1, 0)


def test_progress_tracker_partial_completion(temp_dir):
    """Test progress tracker with partial completion."""
    tracker = ProgressTracker(temp_dir)
    
    # Create partially completed file (similar to your Claude issue)
    partial_data = {
        "metadata": {
            "model_name": "TestModel",
            "config_version": 1,
            "timestamp": "2025-05-24T05:58:24.994068Z",
            "last_updated": "2025-05-24T06:08:45.981340Z",
            "global_settings": {}
        },
        "sequences": {
            "TestSequence1": {
                "run_1": [
                    {"prompt_name": "Prompt1", "response": "Response 1", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:24.994068Z"},
                    {"prompt_name": "Prompt2", "response": "Response 2", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:25.994068Z"}
                ],
                "run_2": [
                    {"prompt_name": "Prompt1", "response": "Response 3", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:26.994068Z"},
                    {"prompt_name": "Prompt2", "response": "Response 4", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:27.994068Z"}
                ]
            }
            # TestSequence2 is missing - this simulates your Claude issue
        },
        "evaluation_scores": {},
        "status": "in_progress"
    }
    
    # Save partial data
    result_path = tracker.get_result_file_path("TestModel", "testhash")
    with open(result_path, 'w') as f:
        json.dump(partial_data, f, indent=2)
    
    sequences = ["TestSequence1", "TestSequence2"]
    prompts_per_sequence = {"TestSequence1": 2, "TestSequence2": 1}
    
    # Should not be complete (missing TestSequence2)
    assert not tracker.is_complete("TestModel", "testhash", sequences, 2, prompts_per_sequence)
    
    # Should get next task (TestSequence2, run 1, prompt 0)
    next_task = tracker.get_next_task("TestModel", "testhash", sequences, 2, prompts_per_sequence)
    assert next_task == ("TestSequence2", 1, 0)


def test_progress_tracker_complete(temp_dir):
    """Test progress tracker with complete data."""
    tracker = ProgressTracker(temp_dir)
    
    # Create fully completed file
    complete_data = {
        "metadata": {
            "model_name": "TestModel",
            "config_version": 1,
            "timestamp": "2025-05-24T05:58:24.994068Z",
            "last_updated": "2025-05-24T06:08:45.981340Z",
            "global_settings": {}
        },
        "sequences": {
            "TestSequence1": {
                "run_1": [
                    {"prompt_name": "Prompt1", "response": "Response 1", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:24.994068Z"},
                    {"prompt_name": "Prompt2", "response": "Response 2", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:25.994068Z"}
                ],
                "run_2": [
                    {"prompt_name": "Prompt1", "response": "Response 3", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:26.994068Z"},
                    {"prompt_name": "Prompt2", "response": "Response 4", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:27.994068Z"}
                ]
            },
            "TestSequence2": {
                "run_1": [
                    {"prompt_name": "Prompt3", "response": "Response 5", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:28.994068Z"}
                ],
                "run_2": [
                    {"prompt_name": "Prompt3", "response": "Response 6", "generation_time": 0.1, "completed_at": "2025-05-24T05:58:29.994068Z"}
                ]
            }
        },
        "evaluation_scores": {},
        "status": "complete"
    }
    
    # Save complete data
    result_path = tracker.get_result_file_path("TestModel", "testhash")
    with open(result_path, 'w') as f:
        json.dump(complete_data, f, indent=2)
    
    sequences = ["TestSequence1", "TestSequence2"]
    prompts_per_sequence = {"TestSequence1": 2, "TestSequence2": 1}
    
    # Should be complete
    assert tracker.is_complete("TestModel", "testhash", sequences, 2, prompts_per_sequence)
    
    # Should get no next task
    next_task = tracker.get_next_task("TestModel", "testhash", sequences, 2, prompts_per_sequence)
    assert next_task is None


if __name__ == "__main__":
    # Run tests manually for debugging
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    try:
        print("Testing empty progress tracker...")
        test_progress_tracker_empty(temp_dir)
        print("✓ Empty tracker test passed")
        
        print("Testing partial completion...")
        test_progress_tracker_partial_completion(temp_dir)
        print("✓ Partial completion test passed")
        
        print("Testing complete data...")
        test_progress_tracker_complete(temp_dir)
        print("✓ Complete data test passed")
        
        print("All tests passed!")
        
    finally:
        shutil.rmtree(temp_dir)
