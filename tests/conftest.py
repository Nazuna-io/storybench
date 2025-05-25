"""
Test configuration and fixtures for the comprehensive backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

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
            client = TestClient(app)
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
