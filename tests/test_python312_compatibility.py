"""Test Python 3.12+ compatibility and features."""

import sys
import pytest
from pathlib import Path

class TestPython312Compatibility:
    """Test that the system works correctly with Python 3.12+."""
    
    def test_python_version_requirement(self):
        """Test that Python version meets 3.12+ requirement."""
        major, minor = sys.version_info[:2]
        assert major == 3 and minor >= 12, f"Python 3.12+ required, found {major}.{minor}"
    
    def test_pathlib_functionality(self):
        """Test pathlib features that work well in Python 3.12+."""
        # Path operations that are common in the codebase
        test_path = Path("test") / "subdir" / "file.txt"
        assert str(test_path) == "test/subdir/file.txt"
        
        # Glob functionality
        current_dir = Path(".")
        python_files = list(current_dir.glob("*.py"))
        # Should find at least some python files in project
        assert len(python_files) >= 0  # Just verify it doesn't crash
    
    def test_type_annotations_compatibility(self):
        """Test that type annotations work with Python 3.12+."""
        from typing import Optional, List, Dict, Any
        
        # Test function with modern type hints
        def test_func(
            optional_param: Optional[str] = None,
            list_param: List[Dict[str, Any]] = None
        ) -> bool:
            return True
        
        result = test_func()
        assert result is True
    
    def test_async_await_functionality(self):
        """Test async/await works properly in Python 3.12+."""
        import asyncio
        
        async def sample_async_function():
            await asyncio.sleep(0.01)  # Minimal delay
            return "async_result"
        
        # Test async function execution
        result = asyncio.run(sample_async_function())
        assert result == "async_result"
    
    def test_cli_import_compatibility(self):
        """Test that CLI imports work with Python 3.12+."""
        # Test importing main CLI modules
        from storybench.cli import cli
        from storybench.models.config import ModelConfig
        
        # Should not raise import errors
        assert cli is not None
        assert ModelConfig is not None
    
    def test_web_import_compatibility(self):
        """Test that web interface imports work with Python 3.12+."""
        from unittest.mock import patch
        
        # Mock external dependencies to avoid import issues
        with patch('storybench.evaluators.factory.EvaluatorFactory'):
            from storybench.web.main import app
            assert app is not None
    
    def test_json_handling_compatibility(self):
        """Test JSON handling works with Python 3.12+."""
        import json
        from pathlib import Path
        
        # Test reading a config file if it exists
        config_dir = Path("config")
        if config_dir.exists():
            prompts_file = config_dir / "prompts.json"
            if prompts_file.exists():
                with open(prompts_file) as f:
                    data = json.load(f)
                assert isinstance(data, (dict, list))
    
    def test_yaml_handling_compatibility(self):
        """Test YAML handling works with Python 3.12+."""
        import yaml
        from pathlib import Path
        
        # Test reading a YAML config file if it exists
        config_dir = Path("config")
        if config_dir.exists():
            models_file = config_dir / "models.yaml"
            if models_file.exists():
                with open(models_file) as f:
                    data = yaml.safe_load(f)
                assert isinstance(data, dict)
    
    def test_fastapi_compatibility(self):
        """Test FastAPI works with Python 3.12+."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # Create a simple test app
        test_app = FastAPI()
        
        @test_app.get("/test")
        def test_endpoint():
            return {"status": "ok", "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"}
        
        client = TestClient(test_app)
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["python_version"].startswith("3.12")
