"""
Comprehensive Unit Tests for Storybench Backend Services
Tests individual components with high coverage
"""
import pytest
import tempfile
import os
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the services to test
import sys
sys.path.append('src')

from storybench.web.services.config_service import ConfigService
from storybench.web.services.validation_service import ValidationService
from storybench.web.services.eval_service import EvaluationService
from storybench.web.services.results_service import ResultsService

class TestConfigService:
    """Test ConfigService functionality"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            
            # Create mock config files
            models_config = {
                "models": [
                    {
                        "name": "test-model",
                        "type": "api", 
                        "provider": "openai",
                        "model_name": "gpt-3.5-turbo"
                    }
                ]
            }
            
            prompts_config = {
                "sequences": {
                    "TestSequence": {
                        "prompts": ["Test prompt 1", "Test prompt 2"]
                    }
                }
            }
            
            criteria_config = {
                "criteria": {
                    "creativity": {"weight": 1.0},
                    "coherence": {"weight": 1.0}
                }
            }
            
            # Write config files
            with open(config_dir / "models.yaml", "w") as f:
                yaml.dump(models_config, f)
                
            with open(config_dir / "prompts.json", "w") as f:
                json.dump(prompts_config, f)
                
            with open(config_dir / "evaluation_criteria.yaml", "w") as f:
                yaml.dump(criteria_config, f)
                
            yield str(config_dir)
    
    def test_load_models_config(self, temp_config_dir):
        """Test loading models configuration"""
        with patch('storybench.web.services.config_service.Path') as mock_path:
            mock_path.return_value = Path(temp_config_dir)
            
            service = ConfigService()
            config = service.load_models_config()
            
            assert "models" in config
            assert len(config["models"]) == 1
            assert config["models"][0]["name"] == "test-model"
    
    def test_load_prompts_config(self, temp_config_dir):
        """Test loading prompts configuration"""
        with patch('storybench.web.services.config_service.Path') as mock_path:
            mock_path.return_value = Path(temp_config_dir)
            
            service = ConfigService()
            config = service.load_prompts_config()
            
            assert "sequences" in config
            assert "TestSequence" in config["sequences"]
    
    def test_save_models_config(self, temp_config_dir):
        """Test saving models configuration"""
        with patch('storybench.web.services.config_service.Path') as mock_path:
            mock_path.return_value = Path(temp_config_dir)
            
            service = ConfigService()
            
            new_config = {
                "models": [
                    {
                        "name": "new-model",
                        "type": "local",
                        "repo_id": "test/model"
                    }
                ]
            }
            
            service.save_models_config(new_config)
            
            # Verify it was saved
            loaded_config = service.load_models_config()
            assert loaded_config["models"][0]["name"] == "new-model"
    
    def test_config_file_not_found(self):
        """Test handling of missing config files"""
        with patch('storybench.web.services.config_service.Path') as mock_path:
            mock_path.return_value = Path("/nonexistent")
            
            service = ConfigService()
            
            # Should return default/empty config without crashing
            config = service.load_models_config()
            assert isinstance(config, dict)

class TestValidationService:
    """Test ValidationService functionality"""
    
    @pytest.fixture
    def validation_service(self):
        """Create ValidationService instance"""
        return ValidationService()
    
    def test_validate_model_config_valid(self, validation_service):
        """Test validation of valid model configuration"""
        valid_config = {
            "models": [
                {
                    "name": "test-model",
                    "type": "api",
                    "provider": "openai", 
                    "model_name": "gpt-3.5-turbo"
                }
            ]
        }
        
        result = validation_service.validate_models_config(valid_config)
        assert result["valid"] == True
        assert len(result["errors"]) == 0
    
    def test_validate_model_config_invalid(self, validation_service):
        """Test validation of invalid model configuration"""
        invalid_config = {
            "models": [
                {
                    "name": "",  # Invalid empty name
                    "type": "invalid_type",  # Invalid type
                }
            ]
        }
        
        result = validation_service.validate_models_config(invalid_config)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
    
    def test_validate_prompts_config_valid(self, validation_service):
        """Test validation of valid prompts configuration"""
        valid_config = {
            "sequences": {
                "TestSequence": {
                    "prompts": ["Prompt 1", "Prompt 2"]
                }
            }
        }
        
        result = validation_service.validate_prompts_config(valid_config)
        assert result["valid"] == True
    
    def test_validate_prompts_config_invalid(self, validation_service):
        """Test validation of invalid prompts configuration"""
        invalid_config = {
            "sequences": {
                "": {  # Invalid empty sequence name
                    "prompts": []  # Invalid empty prompts
                }
            }
        }
        
        result = validation_service.validate_prompts_config(invalid_config)
        assert result["valid"] == False
    
    @patch('requests.get')
    def test_validate_api_connection_success(self, mock_get, validation_service):
        """Test successful API connection validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        result = validation_service.validate_api_connection("openai", "test-key")
        assert result["valid"] == True
    
    @patch('requests.get')
    def test_validate_api_connection_failure(self, mock_get, validation_service):
        """Test failed API connection validation"""
        mock_get.side_effect = Exception("Connection failed")
        
        result = validation_service.validate_api_connection("openai", "invalid-key")
        assert result["valid"] == False
        assert "error" in result

class TestEvaluationService:
    """Test EvaluationService functionality"""
    
    @pytest.fixture
    def evaluation_service(self):
        """Create EvaluationService instance"""
        return EvaluationService()
    
    def test_get_status_not_running(self, evaluation_service):
        """Test getting status when no evaluation is running"""
        status = evaluation_service.get_status()
        
        assert "running" in status
        assert status["running"] == False
        assert "current_model" in status
        assert "progress" in status
    
    def test_start_evaluation_validation(self, evaluation_service):
        """Test evaluation start validation"""
        # Test with invalid request
        invalid_request = {}
        
        with pytest.raises(Exception):
            evaluation_service.start_evaluation(invalid_request)
    
    def test_stop_evaluation_when_not_running(self, evaluation_service):
        """Test stopping evaluation when none is running"""
        result = evaluation_service.stop_evaluation()
        
        # Should handle gracefully
        assert isinstance(result, dict)
    
    @patch('storybench.core.progress_tracker.ProgressTracker')
    def test_get_resume_status(self, mock_tracker, evaluation_service):
        """Test getting resume status"""
        # Mock progress tracker
        mock_instance = Mock()
        mock_instance.get_next_task.return_value = None
        mock_tracker.return_value = mock_instance
        
        status = evaluation_service.get_resume_status()
        
        assert "can_resume" in status
        assert isinstance(status["can_resume"], bool)

class TestResultsService:
    """Test ResultsService functionality"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory with mock results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            # Create mock result files
            result1 = {
                "metadata": {
                    "model_name": "test-model-1",
                    "config_version": "abc123",
                    "timestamp": "2025-01-01T00:00:00Z"
                },
                "sequences": {
                    "TestSequence": {
                        "run_1": [{"response": "Test response 1"}]
                    }
                },
                "evaluation_scores": {
                    "overall": 8.5,
                    "creativity": 8.0,
                    "coherence": 9.0
                },
                "status": "completed"
            }
            
            result2 = {
                "metadata": {
                    "model_name": "test-model-2", 
                    "config_version": "def456",
                    "timestamp": "2025-01-02T00:00:00Z"
                },
                "status": "in_progress"
            }
            
            # Write result files
            with open(output_dir / "test-model-1_abc123.json", "w") as f:
                json.dump(result1, f)
                
            with open(output_dir / "test-model-2_def456.json", "w") as f:
                json.dump(result2, f)
                
            yield str(output_dir)
    
    def test_get_all_results(self, temp_output_dir):
        """Test getting all results"""
        with patch('storybench.web.services.results_service.Path') as mock_path:
            mock_path.return_value = Path(temp_output_dir)
            
            service = ResultsService()
            results = service.get_all_results()
            
            assert "results" in results
            assert len(results["results"]) == 2
            
            # Check result structure
            for result in results["results"]:
                assert "model_name" in result
                assert "config_version" in result
                assert "timestamp" in result
                assert "status" in result
    
    def test_get_results_with_filters(self, temp_output_dir):
        """Test getting results with filters"""
        with patch('storybench.web.services.results_service.Path') as mock_path:
            mock_path.return_value = Path(temp_output_dir)
            
            service = ResultsService()
            
            # Filter by status
            results = service.get_all_results(status_filter="completed")
            completed_results = [r for r in results["results"] if r["status"] == "completed"]
            assert len(completed_results) >= 1
    
    def test_get_model_results(self, temp_output_dir):
        """Test getting results for specific model"""
        with patch('storybench.web.services.results_service.Path') as mock_path:
            mock_path.return_value = Path(temp_output_dir)
            
            service = ResultsService()
            result = service.get_model_results("test-model-1")
            
            assert result is not None
            assert result["metadata"]["model_name"] == "test-model-1"
    
    def test_get_nonexistent_model_results(self, temp_output_dir):
        """Test getting results for non-existent model"""
        with patch('storybench.web.services.results_service.Path') as mock_path:
            mock_path.return_value = Path(temp_output_dir)
            
            service = ResultsService()
            result = service.get_model_results("nonexistent-model")
            
            assert result is None
    
    def test_get_available_versions(self, temp_output_dir):
        """Test getting available configuration versions"""
        with patch('storybench.web.services.results_service.Path') as mock_path:
            mock_path.return_value = Path(temp_output_dir)
            
            service = ResultsService()
            versions = service.get_available_versions()
            
            assert "versions" in versions
            assert len(versions["versions"]) >= 2
            assert "abc123" in [v["version"] for v in versions["versions"]]
            assert "def456" in [v["version"] for v in versions["versions"]]

class TestIntegrationBetweenServices:
    """Test integration between different services"""
    
    def test_config_to_validation_integration(self, temp_config_dir):
        """Test integration between ConfigService and ValidationService"""
        with patch('storybench.web.services.config_service.Path') as mock_path:
            mock_path.return_value = Path(temp_config_dir)
            
            # Load config using ConfigService
            config_service = ConfigService()
            models_config = config_service.load_models_config()
            
            # Validate using ValidationService
            validation_service = ValidationService()
            result = validation_service.validate_models_config(models_config)
            
            # Should validate successfully
            assert result["valid"] == True
    
    def test_results_service_with_evaluation_service(self):
        """Test integration between ResultsService and EvaluationService"""
        results_service = ResultsService()
        eval_service = EvaluationService()
        
        # Get evaluation status
        eval_status = eval_service.get_status()
        
        # Get results
        results = results_service.get_all_results()
        
        # Both should work without errors
        assert isinstance(eval_status, dict)
        assert isinstance(results, dict)

class TestErrorHandling:
    """Test error handling across services"""
    
    def test_config_service_file_permissions(self):
        """Test ConfigService handling of file permission errors"""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            service = ConfigService()
            
            # Should handle permission errors gracefully
            config = service.load_models_config()
            assert isinstance(config, dict)
    
    def test_validation_service_network_errors(self):
        """Test ValidationService handling of network errors"""
        service = ValidationService()
        
        with patch('requests.get', side_effect=Exception("Network error")):
            result = service.validate_api_connection("openai", "test-key")
            
            assert result["valid"] == False
            assert "error" in result
    
    def test_results_service_corrupted_files(self, temp_output_dir):
        """Test ResultsService handling of corrupted result files"""
        # Create corrupted JSON file
        corrupted_file = Path(temp_output_dir) / "corrupted_result.json"
        with open(corrupted_file, "w") as f:
            f.write("invalid json content {")
            
        with patch('storybench.web.services.results_service.Path') as mock_path:
            mock_path.return_value = Path(temp_output_dir)
            
            service = ResultsService()
            results = service.get_all_results()
            
            # Should handle corrupted files gracefully
            assert isinstance(results, dict)
            assert "results" in results

class TestPerformanceAndScaling:
    """Test performance characteristics"""
    
    def test_results_service_large_dataset(self):
        """Test ResultsService with large number of results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Create many result files
            for i in range(100):
                result = {
                    "metadata": {
                        "model_name": f"model-{i}",
                        "config_version": f"version-{i}",
                        "timestamp": f"2025-01-{i:02d}T00:00:00Z"
                    },
                    "status": "completed"
                }
                
                with open(output_dir / f"model-{i}_version-{i}.json", "w") as f:
                    json.dump(result, f)
            
            with patch('storybench.web.services.results_service.Path') as mock_path:
                mock_path.return_value = output_dir
                
                service = ResultsService()
                
                # Measure performance
                import time
                start_time = time.time()
                results = service.get_all_results()
                end_time = time.time()
                
                # Should complete in reasonable time
                assert end_time - start_time < 5.0  # 5 seconds max
                assert len(results["results"]) == 100
    
    def test_config_service_concurrent_access(self, temp_config_dir):
        """Test ConfigService handling concurrent access"""
        import threading
        import concurrent.futures
        
        def load_config():
            with patch('storybench.web.services.config_service.Path') as mock_path:
                mock_path.return_value = Path(temp_config_dir)
                service = ConfigService()
                return service.load_models_config()
        
        # Test concurrent loads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(load_config) for _ in range(10)]
            results = [future.result() for future in futures]
            
        # All should succeed
        for result in results:
            assert isinstance(result, dict)
            assert "models" in result
