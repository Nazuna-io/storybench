"""Automated tests for local model functionality."""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from storybench.web.services.local_model_service import LocalModelService
from storybench.database.connection import init_database


class TestLocalModelService:
    """Test suite for LocalModelService."""
    
    @pytest_asyncio.fixture
    async def service(self):
        """Create a LocalModelService instance for testing."""
        return LocalModelService(database=None)
    
    @pytest_asyncio.fixture
    async def service_with_db(self):
        """Create a LocalModelService with database connection."""
        try:
            # Set up test database connection
            os.environ.setdefault("MONGODB_URI", 
                "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")
            database = await init_database()
            return LocalModelService(database=database)
        except Exception:
            # Fallback to None if database connection fails
            return LocalModelService(database=None)
    
    @pytest.mark.asyncio
    async def test_configuration_loading(self, service):
        """Test loading local model configuration."""
        config = await service.load_configuration()
        
        assert isinstance(config, dict)
        assert "generation_model" in config
        assert "evaluation_model" in config
        assert "use_local_evaluator" in config
        assert "settings" in config
        
        # Check required fields in generation model
        gen_model = config["generation_model"]
        assert "repo_id" in gen_model
        assert "filename" in gen_model
    
    @pytest.mark.asyncio
    async def test_configuration_saving(self, service):
        """Test saving local model configuration."""
        test_config = {
            "generation_model": {
                "repo_id": "test/repo",
                "filename": "test.gguf",
                "subdirectory": ""
            },
            "evaluation_model": {
                "repo_id": "test/repo",
                "filename": "test.gguf", 
                "subdirectory": ""
            },
            "use_local_evaluator": True,
            "settings": {
                "temperature": 0.9,
                "max_tokens": 1024,
                "num_runs": 2
            }
        }
        
        result = await service.save_configuration(test_config)
        assert result["success"] is True
        
        # Verify the configuration was saved
        loaded_config = await service.load_configuration()
        assert loaded_config["generation_model"]["repo_id"] == "test/repo"
        assert loaded_config["settings"]["temperature"] == 0.9
    
    @pytest.mark.asyncio
    async def test_hardware_info(self, service):
        """Test hardware information retrieval."""
        info = await service.get_hardware_info()
        
        assert isinstance(info, dict)
        assert "gpu_available" in info
        assert "cpu_cores" in info
        assert "ram_gb" in info
        
        if info["gpu_available"]:
            assert "gpu_name" in info
            assert "vram_gb" in info
    
    def test_callback_registration(self):
        """Test callback registration and unregistration."""
        service = LocalModelService(database=None)
        
        def test_callback(message, message_type="info"):
            pass
        
        # Test output callback
        service.register_output_callback(test_callback)
        assert test_callback in service._output_callbacks
        
        service.unregister_output_callback(test_callback)
        assert test_callback not in service._output_callbacks
        
        # Test progress callback
        service.register_progress_callback(test_callback)
        assert test_callback in service._progress_callbacks
        
        service.unregister_progress_callback(test_callback)
        assert test_callback not in service._progress_callbacks


class TestLocalModelIntegration:
    """Integration tests for local model system."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tiny_model_evaluation_without_db(self):
        """Test end-to-end evaluation with TinyLLama without database."""
        service = LocalModelService(database=None)
        
        # Track console messages
        messages = []
        def capture_output(message, message_type="info"):
            messages.append((message_type, message))
        
        service.register_output_callback(capture_output)
        
        # Configuration for TinyLLama
        test_config = {
            "generation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "evaluation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "use_local_evaluator": False,
            "settings": {
                "temperature": 1.0,
                "max_tokens": 50,  # Small response for testing
                "num_runs": 1,
                "vram_limit_percent": 80,
                "auto_evaluate": False  # Skip evaluation for speed
            }
        }
        
        # Run evaluation
        await service.run_local_evaluation(
            generation_model=test_config["generation_model"],
            evaluation_model=test_config["evaluation_model"],
            use_local_evaluator=False,
            sequences=["FilmNarrative"],
            settings=test_config["settings"],
            api_keys={}
        )
        
        # Verify messages were captured
        assert len(messages) > 0
        
        # Check for expected message types
        message_types = [msg[0] for msg in messages]
        assert "info" in message_types
        assert "output" in message_types
        
        # Check for expected content
        message_texts = [msg[1] for msg in messages]
        assert any("Starting evaluation" in msg for msg in message_texts)
        assert any("Generation model ready" in msg for msg in message_texts)
        assert any("Response generated" in msg for msg in message_texts)
        assert any("Evaluation completed" in msg for msg in message_texts)
    
    @pytest.mark.asyncio 
    @pytest.mark.slow
    async def test_tiny_model_evaluation_with_db(self):
        """Test end-to-end evaluation with TinyLLama with database."""
        try:
            # Set up database connection
            os.environ.setdefault("MONGODB_URI", 
                "mongodb+srv://todd:FyilOF4jed0bFUxO@storybench-cluster0.o0tp9zz.mongodb.net/?retryWrites=true&w=majority&appName=Storybench-cluster0")
            database = await init_database()
            service = LocalModelService(database=database)
        except Exception:
            # Skip test if database connection fails
            pytest.skip("Database connection not available")
        
        # Track console messages
        messages = []
        def capture_output(message, message_type="info"):
            messages.append((message_type, message))
        
        service.register_output_callback(capture_output)
        
        # Configuration for TinyLLama
        test_config = {
            "generation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "evaluation_model": {
                "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
                "subdirectory": ""
            },
            "use_local_evaluator": False,
            "settings": {
                "temperature": 1.0,
                "max_tokens": 50,  # Small response for testing
                "num_runs": 1,
                "vram_limit_percent": 80,
                "auto_evaluate": False  # Skip evaluation for speed
            }
        }
        
        # Run evaluation
        await service.run_local_evaluation(
            generation_model=test_config["generation_model"],
            evaluation_model=test_config["evaluation_model"],
            use_local_evaluator=False,
            sequences=["FilmNarrative"],
            settings=test_config["settings"],
            api_keys={}
        )
        
        # Verify messages were captured
        assert len(messages) > 0
        
        # Check for database storage success
        message_texts = [msg[1] for msg in messages]
        assert any("Stored" in msg and "responses in database" in msg for msg in message_texts)


class TestLocalModelWebAPI:
    """Tests for the web API endpoints."""
    
    def test_placeholder(self):
        """Placeholder test for web API - requires FastAPI test client setup."""
        # TODO: Implement web API tests with FastAPI TestClient
        # This would test the endpoints in local_models.py
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
