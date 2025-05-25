"""
Test configuration and fixtures for the comprehensive backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

async def seed_test_data(database):
    """Seed the test database with basic configuration data."""
    from storybench.database.services.config_service import ConfigService
    
    config_service = ConfigService(database)
    
    # Sample models configuration - models should be a list of ModelConfigItem
    models_data = {
        "models": [
            {
                "name": "gpt-4",
                "type": "api",
                "provider": "openai",
                "model_name": "gpt-4"
            }
        ],
        "evaluation": {
            "auto_evaluate_generated_responses": True,
            "evaluator_llm_names": ["gpt-4"],
            "max_retries_on_evaluation_failure": 3
        }
    }
    
    # Sample prompts configuration - should use sequences format
    prompts_data = {
        "sequences": {
            "creativity_test": [
                {
                    "name": "creativity_prompt",
                    "text": "You are a creativity evaluator. Evaluate the creativity of: {content}"
                }
            ],
            "coherence_test": [
                {
                    "name": "coherence_prompt", 
                    "text": "You are a coherence evaluator. Evaluate the coherence of: {content}"
                }
            ]
        }
    }
    
    # Save configurations
    try:
        await config_service.save_models_config(models_data)
        await config_service.save_prompts_config(prompts_data)
        print("Test data seeded successfully")
    except Exception as e:
        print(f"Failed to seed test data: {e}")

# Create a fixture that provides a TestClient instead of using requests to localhost
@pytest.fixture
def client():
    """Provide a TestClient for testing the FastAPI app."""
    # Mock any external dependencies that might cause import issues
    with patch('storybench.evaluators.factory.EvaluatorFactory') as mock_factory:
        # Mock the factory to avoid API key requirements
        mock_factory.return_value = MagicMock()
        
        try:
            from storybench.web.main import app
            from storybench.database.connection import init_database, close_database, get_database
            
            # For tests, use the Atlas connection string with a test database name
            # This overrides the MONGODB_TEST_URI which points to localhost
            atlas_uri = os.getenv("MONGODB_URI")
            if not atlas_uri:
                pytest.skip("MONGODB_URI not found in environment variables")
            
            # Use a test database name to avoid conflicts with production data
            test_database_name = "storybench_test"
            
            # Manually initialize database for tests since TestClient doesn't trigger lifespan
            async def setup_db():
                await init_database(connection_string=atlas_uri, database_name=test_database_name)
                # Seed test data
                database = await get_database()
                await seed_test_data(database)
            
            async def cleanup_db():
                # Clean up test data before closing
                try:
                    database = await get_database()
                    # Drop test collections
                    await database.models.drop()
                    await database.prompts.drop()
                    await database.evaluation_criteria.drop()
                except Exception as e:
                    print(f"Error cleaning up test data: {e}")
                await close_database()
            
            # Run database setup
            asyncio.run(setup_db())
            
            client = TestClient(app)
            
            # Schedule cleanup (this will run when the fixture is torn down)
            def cleanup():
                asyncio.run(cleanup_db())
            
            # Add cleanup to the client object so it gets called when the fixture is destroyed
            client._cleanup = cleanup
            
            return client
        except ImportError as e:
            pytest.skip(f"Could not import FastAPI app: {e}")

@pytest.fixture
def mock_evaluation_service():
    """Mock evaluation service to avoid external dependencies."""
    with patch('storybench.web.api.evaluations._eval_service') as mock_service:
        mock_service.status = "idle"
        mock_service.progress = 0
        mock_service.total_tests = 0
        mock_service.current_test = ""
        yield mock_service
