
import time
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

class TestAPIPerformance:
    """API performance tests"""
    
    def test_health_endpoint_response_time(self, client):
        """Test health endpoint responds quickly"""
        start_time = time.time()
        response = client.get("/api/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"Health endpoint took {response_time:.2f}s"
        
    def test_results_endpoint_response_time(self, client):
        """Test results endpoint performance"""
        start_time = time.time()
        response = client.get("/api/results")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0, f"Results endpoint took {response_time:.2f}s"
        
    def test_concurrent_requests(self, client):
        """Test API handles concurrent requests well"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


class TestDataIntegrity:
    """Data integrity and consistency tests"""
    
    def test_config_consistency(self, client):
        """Test configuration endpoints return consistent data"""
        models_response = client.get("/api/config/models")
        prompts_response = client.get("/api/config/prompts")
        
        assert models_response.status_code == 200
        assert prompts_response.status_code == 200
        
        # Basic structure validation
        models_data = models_response.json()
        prompts_data = prompts_response.json()
        
        assert isinstance(models_data, (list, dict))
        assert isinstance(prompts_data, (list, dict))
        
    def test_results_data_structure(self, client):
        """Test results endpoint returns properly structured data"""
        response = client.get("/api/results")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, (list, dict))


class TestSecurityBasics:
    """Basic security tests"""
    
    def test_no_sensitive_info_in_responses(self, client):
        """Test that responses don't leak sensitive information"""
        endpoints = ["/api/health", "/api/results", "/api/config/models"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                content = response.text.lower()
                # Check for common sensitive patterns (but avoid false positives)
                sensitive_patterns = ['password', 'secret', 'api_key', 'bearer_token']
                for pattern in sensitive_patterns:
                    assert pattern not in content, f"Sensitive info '{pattern}' found in {endpoint}"
        
    def test_request_size_limits(self, client):
        """Test that API properly handles large requests"""
        # Test with reasonable payload
        large_payload = {"data": "x" * 1000}  # 1KB payload
        response = client.post("/api/config/validate", json=large_payload)
        # Should either succeed or return proper error, not crash
        assert response.status_code in [200, 400, 413, 422]


class TestAPIDocumentation:
    """API documentation and schema tests"""
    
    def test_openapi_schema_validity(self, client):
        """Test that OpenAPI schema is valid"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
    def test_api_endpoints_documented(self, client):
        """Test that main API endpoints are documented"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        # Check that key endpoints are documented
        expected_endpoints = ["/api/health", "/api/results"]
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} not documented"



class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def test_config_to_results_workflow(self, client, mock_evaluation_service):
        """Test basic workflow from config to results"""
        # 1. Check health
        health_response = client.get("/api/health")
        assert health_response.status_code == 200
        
        # 2. Get configuration
        models_response = client.get("/api/config/models")
        assert models_response.status_code == 200
        
        # 3. Check results (should work even if empty)
        results_response = client.get("/api/results")
        assert results_response.status_code == 200
        
    def test_sse_integration(self, client):
        """Test Server-Sent Events endpoint basic functionality"""
        # SSE endpoints might need special handling
        response = client.get("/api/sse/evaluation-status")
        # Should either work or return proper error
        assert response.status_code in [200, 404, 405]


class TestUtilities:
    """Utility and helper function tests"""
    
    def test_api_version_consistency(self, client):
        """Test API version consistency across endpoints"""
        health_response = client.get("/api/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            assert "service" in health_data
            
    def test_content_type_headers(self, client):
        """Test proper content-type headers"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestBasicLoad:
    """Basic load testing"""
    
    def test_repeated_requests(self, client):
        """Test API handles repeated requests"""
        for i in range(20):
            response = client.get("/api/health")
            assert response.status_code == 200
            
    def test_rapid_sse_connections(self, client):
        """Test rapid SSE connection attempts"""
        # Test multiple rapid connections to SSE endpoint
        for i in range(5):
            response = client.get("/api/sse/evaluation-status")
            # Should handle gracefully
            assert response.status_code in [200, 404, 405, 429]


class TestAuthentication:
    """Authentication and authorization tests"""
    
    def test_no_auth_required_for_basic_endpoints(self, client):
        """Test that basic endpoints don't require authentication"""
        public_endpoints = ["/api/health", "/api/results"]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            # Should not return 401/403 for public endpoints
            assert response.status_code not in [401, 403]
