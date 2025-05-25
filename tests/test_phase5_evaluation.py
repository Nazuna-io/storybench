"""Test Phase 5 evaluation endpoints."""

import pytest
import requests
import json
import time

BASE_URL = "http://localhost:8000"
SERVER_WAIT_TIMEOUT = 15  # seconds for server to be ready
API_TIMEOUT = 10 # seconds for API calls

def wait_for_server(url, timeout):
    """Wait for server to be available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/api/health", timeout=2)
            if response.status_code == 200:
                print(f"Server at {url} is ready.")
                return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            time.sleep(1)
    print(f"Server at {url} did not become ready within {timeout}s.")
    return False

@pytest.fixture(scope="class")
def backend_server_ready():
    """Fixture to ensure backend server is running before tests in a class."""
    if not wait_for_server(BASE_URL, SERVER_WAIT_TIMEOUT):
        pytest.fail(f"Backend server at {BASE_URL} not responding after {SERVER_WAIT_TIMEOUT}s. Ensure it's running.")

@pytest.mark.usefixtures("backend_server_ready")
class TestEvaluationEndpoints:
    """Test evaluation management endpoints."""
    
    @pytest.mark.integration
    def test_evaluation_status_endpoint(self):
        """Test evaluation status endpoint returns valid data."""
        response = requests.get(f"{BASE_URL}/api/evaluations/status", timeout=API_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "current_model" in data
        assert "progress" in data
        assert "resume_info" in data
        assert "config_version" in data
        
        # Check progress structure
        progress = data["progress"]
        assert "total_tasks" in progress
        assert "completed_tasks" in progress
        
        # Check resume info structure
        resume_info = data["resume_info"]
        assert "can_resume" in resume_info
        assert "models_completed" in resume_info
        assert "models_in_progress" in resume_info
        assert "models_pending" in resume_info
    
    @pytest.mark.integration
    def test_resume_status_endpoint(self):
        """Test resume status endpoint."""
        response = requests.get(f"{BASE_URL}/api/evaluations/resume-status", timeout=API_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "can_resume" in data
        assert "resume_info" in data
        assert "message" in data
    
    @pytest.mark.integration
    def test_results_endpoint(self):
        """Test results endpoint returns data."""
        response = requests.get(f"{BASE_URL}/api/results", timeout=API_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "versions" in data
        assert "total_count" in data
        
        # If there are results, check structure
        if data["results"]:
            result = data["results"][0]
            assert "model_name" in result
            assert "config_version" in result
            assert "status" in result
            assert "timestamp" in result
            assert "scores" in result
            assert "total_responses" in result
            assert "successful_responses" in result
    
    @pytest.mark.usefixtures("backend_server_ready")
    @pytest.mark.integration
    def test_sse_events_endpoint(self):
        """Test SSE events endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/api/sse/events", headers={"Accept": "text/event-stream"}, stream=True, timeout=API_TIMEOUT)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
