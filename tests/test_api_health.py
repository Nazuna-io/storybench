"""
API health tests for Storybench backend.
"""
import requests
import pytest


@pytest.mark.integration
class TestBackendHealth:
    """Test backend API health and availability."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_health_endpoint(self):
        """Test that health endpoint responds."""
        try:
            response = requests.get(f"{self.BASE_URL}/api/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "storybench-web"
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_models_config_endpoint(self):
        """Test that models config endpoint responds."""
        try:
            response = requests.get(f"{self.BASE_URL}/api/config/models", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "global_settings" in data
            assert "models" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_prompts_endpoint(self):
        """Test that prompts endpoint responds."""
        try:
            response = requests.get(f"{self.BASE_URL}/api/config/prompts", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "prompts" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
