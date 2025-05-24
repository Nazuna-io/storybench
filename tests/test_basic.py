"""Test basic imports and configuration loading."""

import pytest
from pathlib import Path
import sys
import os

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all main modules can be imported."""
    try:
        from storybench.models.config import Config, GlobalSettings, ModelConfig
        from storybench.evaluators.base import BaseEvaluator
        from storybench.evaluators.factory import EvaluatorFactory
        from storybench.models.progress import ProgressTracker
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_config_loading():
    """Test configuration loading."""
    try:
        from storybench.models.config import Config
        
        # Test that we can create a config instance
        config_path = Path(__file__).parent.parent / "config" / "models.yaml"
        if config_path.exists():
            cfg = Config.load_config(str(config_path))
            assert cfg is not None
            assert len(cfg.models) > 0
            assert len(cfg.prompts) > 0
        else:
            pytest.skip("Config file not found")
            
    except Exception as e:
        pytest.fail(f"Config loading failed: {e}")

def test_progress_tracker():
    """Test progress tracker initialization."""
    try:
        from storybench.models.progress import ProgressTracker
        
        tracker = ProgressTracker()
        assert tracker is not None
        assert tracker.results_dir.exists()
        
    except Exception as e:
        pytest.fail(f"Progress tracker test failed: {e}")

if __name__ == "__main__":
    test_imports()
    test_config_loading()
    test_progress_tracker()
    print("✓ All basic tests passed!")
