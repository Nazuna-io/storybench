"""Test Phase 5 evaluation endpoints."""

import pytest
import requests
import json

class TestEvaluationEndpoints:
    """Test evaluation management endpoints."""
    
    @pytest.mark.integration
    def test_evaluation_status_endpoint(self):
        """Test evaluation status endpoint returns valid data."""
        response = requests.get("http://localhost:8000/api/evaluations/status")
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
        response = requests.get("http://localhost:8000/api/evaluations/resume-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "can_resume" in data
        assert "resume_info" in data
        assert "message" in data
    
    @pytest.mark.integration
    def test_results_endpoint(self):
        """Test results endpoint returns data."""
        response = requests.get("http://localhost:8000/api/results")
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
    
    @pytest.mark.integration
    def test_sse_events_endpoint(self):
        """Test SSE events endpoint is accessible."""
        response = requests.get(
            "http://localhost:8000/api/sse/events", 
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=1
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
