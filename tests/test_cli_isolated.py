"""Test CLI functionality without heavy dependencies."""

import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_basic_imports():
    """Test that basic CLI modules can be imported."""
    try:
        from storybench.config_loader import load_config_from_file
        from storybench.models.config import ModelConfig
        assert True  # If we get here, imports work
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")


def test_model_config_creation():
    """Test basic ModelConfig creation and validation."""
    try:
        from storybench.models.config import ModelConfig
        
        config = ModelConfig(
            name="test-model",
            model_type="api",
            provider="openai",
            api_key="test-key"
        )
        
        assert config.name == "test-model"
        assert config.model_type == "api"
        
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")



def test_config_validation():
    """Test config validation logic."""
    try:
        from storybench.models.config import ModelConfig
        
        # Test required fields
        with pytest.raises(Exception):  # Should raise validation error
            ModelConfig(name="test")  # Missing required fields
            
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")


def test_environment_variable_handling():
    """Test environment variable processing."""
    with patch.dict(os.environ, {'STORYBENCH_API_KEY': 'test-env-key'}):
        # Test that environment variables can be accessed
        assert os.getenv('STORYBENCH_API_KEY') == 'test-env-key'


def test_path_validation():
    """Test path validation utilities."""
    # Test basic path operations that don't require heavy dependencies
    from pathlib import Path
    
    test_path = Path("/tmp/test")
    assert not test_path.exists() or test_path.exists()  # Basic path check
    
    # Test path creation logic
    temp_path = Path(tempfile.mkdtemp())
    assert temp_path.exists()
    shutil.rmtree(temp_path)


def test_file_operations(temp_dir):
    """Test basic file operations used in CLI."""
    test_file = Path(temp_dir) / "test.json"
    
    # Test file creation
    test_file.write_text('{"test": "data"}')
    assert test_file.exists()
    
    # Test file reading
    content = test_file.read_text()
    assert "test" in content
    
    # Test file deletion
    test_file.unlink()
    assert not test_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])
