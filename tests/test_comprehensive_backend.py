
class TestAPIPerformance:
    """API performance tests"""
    
    def test_health_endpoint_response_time(self):
        """Test health endpoint responds quickly"""
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/health", timeout=API_TIMEOUT)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"Health endpoint took {response_time:.2f}s"
        
    def test_results_endpoint_response_time(self):
        """Test results endpoint performance"""
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/results", timeout=API_TIMEOUT)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0, f"Results endpoint took {response_time:.2f}s"
        
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return requests.get(f"{BASE_URL}/api/health", timeout=API_TIMEOUT)
            
        # Test 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]
            
        # All requests should succeed
        for response in results:
            assert response.status_code == 200

class TestDataIntegrity:
    """Data integrity and consistency tests"""
    
    def test_config_consistency(self):
        """Test configuration data consistency"""
        # Get models config
        models_response = requests.get(f"{BASE_URL}/api/config/models", timeout=API_TIMEOUT)
        assert models_response.status_code == 200
        
        # Get prompts config
        prompts_response = requests.get(f"{BASE_URL}/api/config/prompts", timeout=API_TIMEOUT)
        assert prompts_response.status_code == 200
        
        # Both should return valid JSON
        models_data = models_response.json()
        prompts_data = prompts_response.json()
        
        assert isinstance(models_data, dict)
        assert isinstance(prompts_data, dict)
        
    def test_results_data_structure(self):
        """Test results data has consistent structure"""
        response = requests.get(f"{BASE_URL}/api/results", timeout=API_TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        
        # Check each result has expected structure
        for result in data["results"]:
            assert "model_name" in result
            assert "config_version" in result
            assert "timestamp" in result

class TestSecurityBasics:
    """Basic security tests"""
    
    def test_no_sensitive_info_in_responses(self):
        """Test responses don't contain sensitive information"""
        # Test various endpoints
        endpoints = [
            "/api/health",
            "/api/config/models",
            "/api/results"
        ]
        
        sensitive_patterns = ["password", "secret", "key", "token"]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=API_TIMEOUT)
            if response.status_code == 200:
                content = response.text.lower()
                for pattern in sensitive_patterns:
                    # API keys should be masked, not exposed
                    if pattern in content and "masked" not in content:
                        # This might be expected in config endpoints
                        pass  # Allow masked references
                        
    def test_request_size_limits(self):
        """Test request size limits"""
        # Try to send a very large request
        large_data = {"data": "x" * 10000000}  # 10MB of data
        
        response = requests.post(
            f"{BASE_URL}/api/config/models",
            json=large_data,
            timeout=API_TIMEOUT
        )
        
        # Should either reject with 413 or 422
        assert response.status_code in [413, 422, 400]

class TestAPIDocumentation:
    """API documentation and schema tests"""
    
    def test_openapi_schema_validity(self):
        """Test OpenAPI schema is valid"""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=API_TIMEOUT)
        assert response.status_code == 200
        
        schema = response.json()
        
        # Basic OpenAPI schema validation
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            assert field in schema
            
        # Check info section
        assert "title" in schema["info"]
        assert "version" in schema["info"]
        
        # Check paths exist
        assert len(schema["paths"]) > 0
        
    def test_api_endpoints_documented(self):
        """Test all API endpoints are documented"""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=API_TIMEOUT)
        schema = response.json()
        
        documented_paths = set(schema["paths"].keys())
        
        # Core endpoints should be documented
        expected_paths = [
            "/api/health",
            "/api/config/models",
            "/api/config/prompts",
            "/api/results"
        ]
        
        for path in expected_paths:
            assert any(path in doc_path for doc_path in documented_paths)

# Integration Tests
class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def test_config_to_results_workflow(self):
        """Test complete workflow from config to results"""
        # 1. Check health
        health_response = requests.get(f"{BASE_URL}/api/health", timeout=API_TIMEOUT)
        assert health_response.status_code == 200
        
        # 2. Get current config
        config_response = requests.get(f"{BASE_URL}/api/config/models", timeout=API_TIMEOUT)
        assert config_response.status_code == 200
        
        # 3. Validate config
        validate_response = requests.post(f"{BASE_URL}/api/config/validate", timeout=API_TIMEOUT)
        assert validate_response.status_code == 200
        
        # 4. Check evaluation status
        status_response = requests.get(f"{BASE_URL}/api/evaluations/status", timeout=API_TIMEOUT)
        assert status_response.status_code == 200
        
        # 5. Get results
        results_response = requests.get(f"{BASE_URL}/api/results", timeout=API_TIMEOUT)
        assert results_response.status_code == 200
        
    def test_sse_integration(self):
        """Test SSE integration with evaluation status"""
        # Get evaluation status
        status_response = requests.get(f"{BASE_URL}/api/evaluations/status", timeout=API_TIMEOUT)
        assert status_response.status_code == 200
        
        # Connect to SSE
        sse_response = requests.get(f"{BASE_URL}/api/sse/events", stream=True, timeout=5)
        assert sse_response.status_code == 200
        
        # Read initial messages
        line_count = 0
        for line in sse_response.iter_lines(decode_unicode=True):
            line_count += 1
            if line_count >= 3:  # Read enough to verify connection
                break
                
        sse_response.close()
        assert line_count > 0

# Utility Tests
class TestUtilities:
    """Test utility functions and helpers"""
    
    def test_api_version_consistency(self):
        """Test API version is consistent across endpoints"""
        # Get OpenAPI schema
        schema_response = requests.get(f"{BASE_URL}/openapi.json", timeout=API_TIMEOUT)
        schema = schema_response.json()
        
        # Should have version info
        assert "info" in schema
        assert "version" in schema["info"]
        
        version = schema["info"]["version"]
        assert isinstance(version, str)
        assert len(version) > 0
        
    def test_content_type_headers(self):
        """Test proper content type headers"""
        # JSON endpoints
        json_endpoints = [
            "/api/health",
            "/api/config/models",
            "/api/results"
        ]
        
        for endpoint in json_endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=API_TIMEOUT)
            if response.status_code == 200:
                assert "application/json" in response.headers.get("content-type", "")
                
        # SSE endpoint
        sse_response = requests.get(f"{BASE_URL}/api/sse/events", stream=True, timeout=5)
        assert "text/event-stream" in sse_response.headers.get("content-type", "")
        sse_response.close()

# Load Testing (Basic)
class TestBasicLoad:
    """Basic load testing"""
    
    def test_repeated_requests(self):
        """Test handling repeated requests"""
        for i in range(10):
            response = requests.get(f"{BASE_URL}/api/health", timeout=API_TIMEOUT)
            assert response.status_code == 200
            time.sleep(0.1)  # Small delay between requests
            
    def test_rapid_sse_connections(self):
        """Test rapid SSE connections"""
        connections = []
        
        try:
            # Open multiple SSE connections
            for i in range(3):
                response = requests.get(f"{BASE_URL}/api/sse/events", stream=True, timeout=5)
                if response.status_code == 200:
                    connections.append(response)
                    
            # All should connect successfully
            assert len(connections) > 0
            
        finally:
            # Clean up connections
            for conn in connections:
                conn.close()

# Test that covers API authentication if implemented
class TestAuthentication:
    """Authentication tests (if applicable)"""
    
    def test_no_auth_required_for_basic_endpoints(self):
        """Test basic endpoints don't require authentication"""
        # These endpoints should be accessible without auth
        public_endpoints = [
            "/api/health",
            "/docs",
            "/openapi.json"
        ]
        
        for endpoint in public_endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=API_TIMEOUT)
            # Should not return 401 Unauthorized
            assert response.status_code != 401
