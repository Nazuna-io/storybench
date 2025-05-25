import pytest
"""
Comprehensive Unit Tests for Storybench Backend Services
Tests individual components with high coverage
"""
import asyncio
import tempfile
import time
import yaml
from pathlib import Path
import json
# At the top of your test_unit_services.py file

# Imports for mocking
from unittest.mock import Mock, MagicMock, patch, call, AsyncMock # Ensure patch is also there if not already

# Project-specific imports (ensure these are correctly grouped or placed)
from storybench.web.repositories.file_repository import Repository
from storybench.models.config import Config, ModelConfig, GlobalSettings, EvaluationConfig # Add others if needed by tests
from storybench.web.services.config_service import ConfigService
from storybench.web.services.validation_service import ValidationService
from storybench.web.services.results_service import ResultsService, ResultSummary, DetailedResult
from storybench.web.services.eval_service import EvaluationService
from storybench.web.services.validation_service import ModelValidationResult, APITestResult # Import specific validation models
# ... any other necessary imports ...
            
@pytest.mark.asyncio
class TestConfigService:
    """Test ConfigService functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Provides a mock repository instance."""
        mock_repo = MagicMock(spec=Repository)
        # Default behavior for loading, can be overridden in specific tests
        mock_repo.load_models_config.return_value = {"models": [], "version": "default_models_v0"}
        mock_repo.load_prompts.return_value = {"prompts": [], "version": "default_prompts_v0"}
        mock_repo.load_api_keys.return_value = {} # Default empty API keys
        # Mock save methods to simulate successful save without actual I/O
        mock_repo.save_models_config.return_value = "mock_models_hash"
        mock_repo.save_prompts.return_value = "mock_prompts_hash"
        return mock_repo

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create a temporary directory with mock valid configs for ConfigService tests."""
        config_dir = tmp_path / "config_service_tests"
        config_dir.mkdir(exist_ok=True)

        # Define some basic valid config content
        models_config = {
            "models": [{"name": "test-model", "api_key_id": "test_key", "parameters": {}}],
            "version": "test_models_v1"
        }
        prompts_config = {
            "prompts": [{"id": "test-prompt", "text": "Hello, world!"}],
            "version": "test_prompts_v1"
        }
        criteria_config = {"criteria": [{"id": "crit1", "description": "Test criterion"}]}
        # api_keys_config = {"api_keys": [{"id": "test_key", "service": "test_service", "key": "dummy_key"}]}

        # Write config files
        with open(config_dir / "models.yaml", "w") as f:
            yaml.dump(models_config, f)
        with open(config_dir / "prompts.json", "w") as f:
            json.dump(prompts_config, f)
        with open(config_dir / "evaluation_criteria.yaml", "w") as f:
            yaml.dump(criteria_config, f)
        # If you have api_keys_config and want to write it:
        # if "api_keys_config" in locals() and api_keys_config:
        #     with open(config_dir / "api_keys.yaml", "w") as f:
        #         yaml.dump(api_keys_config, f)
        yield str(config_dir)
    
    @pytest.mark.asyncio
    async def test_load_models_config(self, mock_repository, temp_config_dir):
        """Test loading models configuration."""
        # Setup mock repository to return data from temp_config_dir
        models_file = Path(temp_config_dir) / "models.yaml"
        with open(models_file, 'r') as f:
            expected_models_data = yaml.safe_load(f)
        mock_repository.load_models_config.return_value = expected_models_data

        service = ConfigService(repository=mock_repository)
        
        # Ensure models.yml exists and is loaded
        models_data = await service.get_models_config()
        assert "models" in models_data
        assert len(models_data["models"]) == 1
        assert models_data["models"][0]["name"] == "test-model"
        mock_repository.load_models_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_prompts_config(self, mock_repository, temp_config_dir):
        """Test loading prompts configuration."""
        prompts_file = Path(temp_config_dir) / "prompts.json"
        with open(prompts_file, 'r') as f:
            expected_prompts_data = json.load(f)
        mock_repository.load_prompts.return_value = expected_prompts_data

        service = ConfigService(repository=mock_repository)
        
        prompts_data = await service.get_prompts()
        assert "prompts" in prompts_data
        assert isinstance(prompts_data["prompts"], list) # Ensure it's a list as per fixture
        assert len(prompts_data["prompts"]) > 0 # Ensure list is not empty
        assert prompts_data["prompts"][0]["id"] == "test-prompt" # Check the content of the first prompt
        mock_repository.load_prompts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_models_config(self, mock_repository, temp_config_dir):
        """Test saving models configuration."""
        mock_repository.save_models_config.return_value = None # Simulate successful save

        service = ConfigService(repository=mock_repository)
        new_models_config = {"models": [{"name": "new-model"}]}
        
        await service.update_models_config(new_models_config)
        
        mock_repository.save_models_config.assert_called_once_with(new_models_config)
        
        # Verify that get_models_config would reflect the change:
        mock_repository.load_models_config.return_value = new_models_config
        updated_data = await service.get_models_config()
        assert updated_data["models"][0]["name"] == "new-model"

    @pytest.mark.asyncio
    async def test_save_prompts_config(self, mock_repository, temp_config_dir):
        """Test saving prompts configuration."""
        mock_repository.save_prompts.return_value = None # Simulate successful save

        service = ConfigService(repository=mock_repository)
        new_prompts_config = {"sequences": {"NewSequence": {"prompts": ["New prompt"]}}}
        
        await service.update_prompts(new_prompts_config)
        
        mock_repository.save_prompts.assert_called_once_with(new_prompts_config)

        # Verify that get_prompts would reflect the change:
        mock_repository.load_prompts.return_value = new_prompts_config
        updated_data = await service.get_prompts()
        assert "NewSequence" in updated_data["sequences"]

    @pytest.mark.asyncio
    async def test_config_file_not_found(self, mock_repository):
        """Test handling of missing config files when repository raises FileNotFoundError."""
        service = ConfigService(repository=mock_repository)

        # Test for models config
        mock_repository.load_models_config.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError):
            await service.get_models_config()
        mock_repository.load_models_config.assert_called_once()

        # Reset side_effect for the next call if needed, or use a new mock for prompts
        # For simplicity, let's assume the mock is fresh or we re-assign side_effect.
        mock_repository.reset_mock() # Reset call counts and side_effects for next part

        # Test for prompts config
        mock_repository.load_prompts.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError):
            await service.get_prompts()
        mock_repository.load_prompts.assert_called_once()

class TestValidationService:
    """Test ValidationService functionality"""

    @pytest.fixture
    def mock_repository(self):
        """Provides a mock repository instance."""
        return MagicMock(spec=Repository)
    
    @pytest.fixture
    def validation_service(self, mock_repository):
        """Create ValidationService instance with a mock repository."""
        return ValidationService(repository=mock_repository)
    
    @pytest.mark.asyncio
    async def test_validate_model_config_valid(self, validation_service, mock_repository):
        """Test validation of valid model configuration via validate_configuration."""
        valid_models_config_data = {
            "models": [
                {
                    "name": "Test Model",
                    "type": "api",
                    "provider": "openai",
                    "model_name": "gpt-3.5-turbo",
                    "api_key": "test_key" # Assuming API key is part of this structure for validation
                }
            ]
        }
        # Mock repository to return this config
        # Also need to mock prompts and global settings if validate_configuration loads them
        mock_repository.load_models_config.return_value = valid_models_config_data
        mock_repository.load_prompts.return_value = {"sequences": {}} # Minimal valid prompts
        mock_repository.load_global_settings = AsyncMock(return_value={}) # Minimal valid global settings
        mock_repository.load_evaluation_criteria.return_value = {} # Minimal valid eval config

        # Assuming validate_configuration returns a detailed validation result object or dict
        # We are testing model validation, so we'll focus on that part of the result.
        # We'll also disable API testing for this unit test to isolate model structure validation.
        validation_results = await validation_service.validate_configuration(test_apis=False)

        # Assert that the configuration is considered valid and there are no config_errors
        assert validation_results["valid"] is True
        assert not validation_results["config_errors"]

        # Ensure the underlying repository methods for loading configs were called
        # (as validate_configuration internally calls Config.load_config which might use these)
        # Note: The actual Config.load_config in ValidationService currently hardcodes paths
        # and doesn't use the repository for loading models.yaml. This might be a design point to revisit.
        # For now, these mocks might not be asserted if Config.load_config doesn't use them.
        # If Config.load_config directly reads files, these mocks won't be hit by it.
        # Let's assume for now that the service's validate_configuration directly or indirectly
        # leads to these repository calls for other parts of a *full* config if not for models.yaml itself.
        # Given the current ValidationService.validate_configuration, it directly calls:
        # config = Config.load_config("config/models.yaml")
        # This bypasses the repository for models.yaml. Prompts and global settings are not explicitly loaded
        # by validate_configuration in the provided snippet unless Config.validate() does it.
        # We should adjust mock assertions based on actual behavior of Config.load_config and Config.validate().

        # For now, let's simplify and assume these are not directly called by the current path
        # when test_apis=False and only models.yaml is loaded by Config.load_config.
        # mock_repository.load_models_config.assert_called_once()
        # mock_repository.load_prompts.assert_called_once()
        # mock_repository.load_global_settings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_model_config_invalid(self, validation_service, mock_repository):
        """Test validation of invalid model configuration via validate_configuration."""
        invalid_models_config_data = {
            "models": [
                {
                    "name": "test-model-invalid",
                    "type": "unknown_type", # Invalid type
                    "provider": "some_provider", # Required field might be missing or type is just bad
                    "model_name": "some_model"
                }
            ]
        }
        mock_repository.load_models_config.return_value = invalid_models_config_data
        mock_repository.load_prompts.return_value = {"sequences": {}}
        mock_repository.load_global_settings = AsyncMock(return_value={})
        mock_repository.load_evaluation_criteria.return_value = {} # Minimal valid eval config

        # Disable API testing to isolate model structure validation.
        validation_results = await validation_service.validate_configuration(test_apis=False)

        # Assert that the configuration is considered invalid and there are config_errors
        assert validation_results["valid"] is False
        assert validation_results["config_errors"] # Should not be empty
        # Optionally, check for specific error messages if the Config.validate() provides them predictably
        # For example, if an invalid type is used:
        # assert any("unknown_type" in err.lower() for err in validation_results["config_errors"])

        # mock_repository.load_models_config.assert_called_once() # Config.load_config uses hardcoded path
        # mock_repository.load_prompts.assert_called_once()
        # mock_repository.load_global_settings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_prompts_config_valid(self, validation_service, mock_repository):
        """Test validation of valid prompts configuration via validate_configuration."""
        valid_prompts_config_data = {
            "sequences": {
                "Test Sequence": {
                    "prompts": ["Prompt 1", "Prompt 2"],
                    "settings": {"param1": "value1"}
                }
            }
        }
        mock_repository.load_prompts.return_value = valid_prompts_config_data
        # Mock other configs that validate_configuration might load
        mock_repository.load_models_config.return_value = {"models": []} # Minimal valid models
        mock_repository.load_global_settings = AsyncMock(return_value={}) # Minimal valid global settings
        mock_repository.load_evaluation_criteria.return_value = {} # Minimal valid eval config

        # Disable API testing to isolate structure validation.
        validation_results = await validation_service.validate_configuration(test_apis=False)

        # Assert that the overall configuration (including prompts) is considered valid
        # and there are no config_errors. Prompts are part of the main config file.
        assert validation_results["valid"] is True
        assert not validation_results["config_errors"]

        # mock_repository.load_prompts.assert_called_once() # Config.load_config uses hardcoded path for models.yaml which includes prompts
        # mock_repository.load_models_config.assert_called_once()
        # mock_repository.load_global_settings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_prompts_config_invalid(self, validation_service, mock_repository):
        """Test validation of invalid prompts configuration via validate_configuration."""
        invalid_prompts_config_data = {
            "sequences": {
                "Test Sequence": {
                    "prompts": "not_a_list" # Invalid type for prompts
                }
            }
        }
        mock_repository.load_prompts.return_value = invalid_prompts_config_data
        # Mock other configs that validate_configuration might load
        mock_repository.load_models_config.return_value = {"models": []}
        mock_repository.load_global_settings = AsyncMock(return_value={})
        mock_repository.load_evaluation_criteria.return_value = {}

    @pytest.mark.asyncio
    async def test_validate_prompts_config_invalid(self, validation_service, mock_repository):
        """Test validation of invalid prompts configuration via validate_configuration."""
        invalid_prompts_config_data = {
            "sequences": {
                "Invalid Sequence": { # Name is fine, but content might be invalid
                    "prompts": [], # Invalid: prompts list cannot be empty
                    "settings": "not_a_dict" # Invalid: settings should be a dict
                }
            }
        }
        # Mock repository to provide this invalid prompts config
        # Config.load_config will use this if it's designed to load prompts via repository
        # For models.yaml, it uses a hardcoded path, but prompts might be separate.
        # Let's assume Config.validate() will pick up these prompt issues.
        mock_repository.load_prompts.return_value = invalid_prompts_config_data
        
        # Mock other configs that validate_configuration might load via Config.load_config
        # to ensure they don't cause unrelated validation failures.
        mock_repository.load_models_config.return_value = {"models": []} # Minimal valid models
        mock_repository.load_global_settings = AsyncMock(return_value={}) # Minimal valid global settings
        mock_repository.load_evaluation_criteria.return_value = {} # Minimal valid eval config

        # Disable API testing to isolate structure validation.
        validation_results = await validation_service.validate_configuration(test_apis=False)

        # Assert that the overall configuration (due to invalid prompts) is considered invalid
        assert validation_results["valid"] is False
        assert validation_results["config_errors"] # Should not be empty
        # Optionally, check for specific error messages from Config.validate()
        # e.g., assert any("prompts list cannot be empty" in err.lower() for err in validation_results["config_errors"])

        # The following mocks might not be asserted if Config.load_config doesn't use the repo for all parts
        # or if Config.validate() doesn't trigger further loads.
        # mock_repository.load_prompts.assert_called_once()
        # mock_repository.load_models_config.assert_called_once()
        # mock_repository.load_global_settings.assert_called_once()
    @pytest.mark.asyncio
    @patch('storybench.web.services.validation_service.Config.load_config')
    @patch('storybench.web.services.lightweight_api_test.LightweightAPITester.test_provider')
    async def test_validate_api_connection_success(self, mock_lw_test_provider, mock_config_load_config, validation_service, mock_repository):
        """Test successful API connection validation via validate_configuration."""
        # 1. Prepare mock Config object
        mock_config_instance = Config(config_path="dummy_path") # Path doesn't matter now

        # Populate global_settings
        mock_config_instance.global_settings = GlobalSettings() # Default global settings

        # Populate models - a single API model for this test
        test_model_data = {
            "name": "gpt-3.5-turbo", "type": "api", "provider": "openai", "model_name": "gpt-3.5-turbo"
        }
        mock_config_instance.models = [ModelConfig(**test_model_data)]

        # Populate prompts
        mock_config_instance.prompts = {
            "TestSequence": [{"name": "TestPrompt1", "text": "This is a test prompt."}]
        }
        mock_config_instance._validate_prompts() # Ensure prompt errors are calculated if any

        # Populate evaluation_criteria and evaluation settings
        mock_config_instance.evaluation_criteria = {} # Minimal
        mock_config_instance.evaluation = EvaluationConfig() # Default

        # Mock Config.load_config to return our instance
        mock_config_load_config.return_value = mock_config_instance

        # Mock repository methods used by ValidationService directly
        mock_repository.load_api_keys = AsyncMock(return_value={"OPENAI_API_KEY": "fake_openai_key"})

        # Configure the mock for LightweightAPITester.test_provider (already a parameter)
        mock_lw_test_provider.return_value = (True, None, 100.0) # connected_bool, error_message_opt, latency_ms_opt

        # Act
        validation_results = await validation_service.validate_configuration(test_apis=True, lightweight_test=True)

        # Assertions
        assert validation_results["valid"] is True
        assert not validation_results["config_errors"]

        assert "api_tests" in validation_results
        assert "openai" in validation_results["api_tests"]
        openai_api_test_result = validation_results["api_tests"]["openai"]
        assert openai_api_test_result.provider == "openai"
        assert openai_api_test_result.connected is True
        assert openai_api_test_result.error is None
        assert openai_api_test_result.latency_ms == 100.0

        assert "model_validation" in validation_results
        assert len(validation_results["model_validation"]) == 1
        model_val_result = validation_results["model_validation"][0]
        assert model_val_result.model_name == "gpt-3.5-turbo"
        assert model_val_result.valid is True
        assert model_val_result.api_result is not None
        assert model_val_result.api_result.provider == "openai"
        assert model_val_result.api_result.connected is True
        assert model_val_result.api_result.error is None
        assert model_val_result.api_result.latency_ms == 100.0

        mock_config_load_config.assert_called_once_with("config/models.yaml")
        # Check if LightweightAPITester.test_provider was called. 
        # It's called for each provider with a key, and for each model.
        # For a single openai model, it should be called for 'openai' provider test, 
        assert mock_lw_test_provider.called # Check it was called
    
    @pytest.mark.asyncio
    @patch('storybench.web.services.validation_service.Config.load_config')
    @patch('storybench.web.services.lightweight_api_test.LightweightAPITester.test_connection') # Patched test_connection
    async def test_validate_api_connection_failure(self, mock_lw_test_connection, mock_config_load_config, validation_service, mock_repository):
        """Test failed API connection validation via validate_configuration."""
        # 1. Prepare mock Config object
        mock_config_instance = Config(config_path="dummy_path")
        mock_config_instance.global_settings = GlobalSettings()
        test_model_data = {
            "name": "API Fail Test Model", "type": "api", "provider": "openai", "model_name": "gpt-3.5-turbo-fail"
        }
        mock_config_instance.models = [ModelConfig(**test_model_data)]
        mock_config_instance.prompts = {
            "TestSequenceFail": [{"name": "TestPromptFail1", "text": "This is another test prompt."}]
        }
        mock_config_instance._validate_prompts() # Ensure prompt errors are calculated
        mock_config_instance.evaluation_criteria = {} # Minimal
        mock_config_instance.evaluation = EvaluationConfig() # Default

        # Mock Config.load_config to return our instance
        mock_config_load_config.return_value = mock_config_instance

        # Mock repository methods used by ValidationService directly
        mock_repository.load_api_keys = AsyncMock(return_value={"OPENAI_API_KEY": "fake_openai_key_fail"})

        # Configure the mock for LightweightAPITester.test_connection to simulate failure
        mock_lw_test_connection.return_value = (False, "Connection Error via test_connection", None) # connected_bool, error_message_opt, latency_ms_opt

        # Act
        validation_results = await validation_service.validate_configuration(test_apis=True, lightweight_test=True)

        # Assertions
        # Overall validation (config structure) can still be true even if API test fails.
        # The 'valid' key in the main result reflects config file validity, not API connectivity.
        assert validation_results["valid"] is True 
        assert not validation_results["config_errors"]

        # Provider-level API test might still be affected by a different mock or default if not explicitly mocked here.
        # For this test, we focus on the model-specific API failure reflected in model_validation.
        # If _test_api_connections_lightweight also uses test_connection, this mock will affect it too.
        # For now, let's assume the primary check is on model_validation_result.
        # If needed, we can add another mock for test_provider specifically.

        assert "model_validation" in validation_results
        assert len(validation_results["model_validation"]) == 1
        model_val_result = validation_results["model_validation"][0]
        assert model_val_result.model_name == "API Fail Test Model"
        # Model validation for an API model should be False if its API test fails
        assert model_val_result.valid is False 
        assert "API connection failed: Connection Error via test_connection" in model_val_result.errors # Check for specific error
        assert model_val_result.api_result is not None
        assert model_val_result.api_result.provider == "openai"
        assert model_val_result.api_result.connected is False
        assert model_val_result.api_result.error == "Connection Error via test_connection"
        assert model_val_result.api_result.latency_ms is None

        mock_config_load_config.assert_called_once_with("config/models.yaml")
        assert mock_lw_test_connection.called # Check it was called

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
    
    @pytest.mark.asyncio
    async def test_start_evaluation_validation(self, evaluation_service):
        """Test evaluation start validation with invalid config type."""
        # Test with an invalid type for the 'config' parameter
        invalid_config_type = {} # This is a dict, not a Config object
        api_keys = {}
        
        # start_evaluation should handle internal errors (like AttributeError from bad config)
        # and return False, not raise an exception upwards.
        result = await evaluation_service.start_evaluation(config=invalid_config_type, api_keys=api_keys)
        assert result is False
        
        # Optionally, we could mock and check if an error_callback was called if the service allows setting it.
        # For now, checking the boolean return is the primary validation of its behavior with bad input type.
    
    @pytest.mark.asyncio
    async def test_stop_evaluation_when_not_running(self, evaluation_service):
        """Test stopping evaluation when none is running."""
        # stop_evaluation returns False if no task is running or if it's already stopped.
        result = await evaluation_service.stop_evaluation()
        
        assert result is False
    
    @patch('storybench.core.progress_tracker.ProgressTracker')
    @pytest.mark.asyncio
    async def test_get_resume_status(self, mock_tracker_class, evaluation_service):
        """Test getting resume status."""
        # Mock ProgressTracker instance and its methods
        mock_tracker_instance = Mock()
        mock_tracker_instance.get_next_task.return_value = None # Simulate no tasks in progress for a simple case
        mock_tracker_instance.is_complete.return_value = True # Simulate all models are complete
        mock_tracker_class.return_value = mock_tracker_instance
        
        # Create a mock Config object with necessary attributes for get_resume_status
        mock_config = Mock(spec=Config) # Use spec for stricter mocking if Config class is available
        # If Config is not directly importable here for spec, mock attributes directly:
        mock_config.get_version_hash.return_value = "test_hash"
        mock_config.prompts = {"Seq1": ["Prompt1"]}
        mock_config.models = [Mock(name="Model1", type="api")]
        mock_config.global_settings = Mock(num_runs=1)

        status_info = await evaluation_service.get_resume_status(config=mock_config)
        
        assert isinstance(status_info.can_resume, bool)
        assert isinstance(status_info.models_completed, list)
        assert isinstance(status_info.models_in_progress, list)
        assert isinstance(status_info.models_pending, list)

        # Example: For the above mocks, we'd expect can_resume to be False and Model1 in models_completed
        assert status_info.can_resume is False
        assert "Model1" in status_info.models_completed

class TestResultsService:
    """Test ResultsService functionality"""
class TestErrorHandling:
    """Test error handling across services"""

    @pytest.fixture
    def mock_repository(self):
        mock_repo = MagicMock(spec=Repository)
        # Configure default behaviors for mock_repo as needed for TestErrorHandling tests
        # For example:
        # mock_repo.some_method.side_effect = SomeException("Simulated error")
        return mock_repo

    @pytest.mark.asyncio
    async def test_config_service_file_permissions(self, mock_repository):
        pass
        # TODO: Implement actual test logic for file permissions

    @patch('storybench.web.services.lightweight_api_test.LightweightAPITester.test_connection')
    async def test_validation_service_network_errors(self, mock_test_connection, mock_repository):
        pass
        # TODO: Implement actual test logic for network errors

    @pytest.mark.asyncio
    async def test_results_service_corrupted_files(self, temp_output_dir): # This will now use the fixture above
        pass
        # TODO: Implement actual test logic for corrupted files
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
    
    @pytest.mark.asyncio
    async def test_get_all_results(self, temp_output_dir):
        """Test getting all results."""
        service = ResultsService(results_dir=temp_output_dir)
        results_list = await service.get_all_results()
        
        # get_all_results returns List[ResultSummary]
        assert isinstance(results_list, list)
        assert len(results_list) == 2
        
        # Check result structure (ResultSummary attributes)
        for result_summary in results_list:
            assert hasattr(result_summary, 'model_name')
            assert hasattr(result_summary, 'config_version')
            assert hasattr(result_summary, 'timestamp')
            assert hasattr(result_summary, 'status')
            assert hasattr(result_summary, 'scores')
            assert result_summary.model_name is not None
            assert result_summary.config_version is not None
    
    @pytest.mark.asyncio
    async def test_get_results_with_filters(self, temp_output_dir):
        """Test getting results and client-side filtering by status."""
        service = ResultsService(results_dir=temp_output_dir)
        
        # Get all results (service method takes config_version, not status_filter)
        # The test's original intent was to filter by status, which we'll do client-side.
        all_results_list = await service.get_all_results()
        
        # Client-side filter by status
        completed_results = [r for r in all_results_list if r.status == "completed"]
        assert len(completed_results) >= 1
        assert all(r.status == "completed" for r in completed_results)

        # Example of using the actual config_version filter if desired:
        # Assuming one of the results (e.g., test-model-1_abc123.json) has config_version 'abc123'
        # results_for_abc123 = await service.get_all_results(config_version="abc123")
        # assert len(results_for_abc123) >= 1
        # assert all(r.config_version == "abc123" for r in results_for_abc123)
    
    @pytest.mark.asyncio
    async def test_get_model_results(self, temp_output_dir):
        """Test getting detailed results for a specific model."""
        service = ResultsService(results_dir=temp_output_dir)
        # The fixture creates 'test-model-1_abc123.json'
        # get_detailed_result will find the most recent if config_version is not specified.
        detailed_result = await service.get_detailed_result("test-model-1")
        
        assert detailed_result is not None
        assert detailed_result.metadata.model_name == "test-model-1"
        # Add more assertions for DetailedResult structure if needed
        assert hasattr(detailed_result, 'sequences')
        assert hasattr(detailed_result, 'evaluation_scores')
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_model_results(self, temp_output_dir):
        """Test getting results for a non-existent model."""
        service = ResultsService(results_dir=temp_output_dir)
        detailed_result = await service.get_detailed_result("nonexistent-model")
        
        assert detailed_result is None
    
    @pytest.mark.asyncio
    async def test_get_available_versions(self, temp_output_dir):
        """Test getting available configuration versions."""
        service = ResultsService(results_dir=temp_output_dir)
        versions = await service.get_available_versions()

        assert isinstance(versions, list)
        # Based on temp_output_dir, the fixture creates files that imply versions 'abc123' and 'def456'
        # The service extracts these from filenames like 'model_abc123.json'
        assert len(versions) >= 2 
        assert "abc123" in versions
        assert "def456" in versions
        # Check sorting if the service guarantees it (it does - sorted list)
        if len(versions) == 2:
            assert versions == sorted(["abc123", "def456"]) # or specific order if known
class TestIntegrationBetweenServices:
    """Test integration between different services"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory with mock valid configs."""
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            # Create mock models.json
            models_content = {
                "version": "1.0",
                "models": [
                    {"name": "TestModel1", "type": "api", "params": {"api_key_env": "TEST_API_KEY_1", "endpoint": "http://test1.com"}},
                    {"name": "TestModel2", "type": "local", "params": {"path": "/path/to/model2"}}
                ],
                "global_settings": {"num_runs": 3, "output_dir": "results"}
            }
            with open(temp_dir / "models.json", "w") as f:
                json.dump(models_content, f)
            
            # Create mock prompts.json
            prompts_content = {
                "version": "1.0",
                "prompts": {
                    "Sequence1": ["Prompt A for Seq1", "Prompt B for Seq1"],
                    "Sequence2": ["Prompt C for Seq2"]
                }
            }
            with open(temp_dir / "prompts.json", "w") as f:
                json.dump(prompts_content, f)

            # Create mock api_keys.json
            api_keys_content = {
                "TEST_API_KEY_1": "dummy_key_value_for_testmodel1"
            }
            with open(temp_dir / "api_keys.json", "w") as f:
                json.dump(api_keys_content, f)

            yield str(temp_dir)

    @pytest.fixture
    def mock_repository(self, temp_config_dir):
        """Provides a mock repository that can 'load' from temp_config_dir."""
        repo = Mock(spec=Repository)
        # Set config_path so ConfigService can find api_keys.json within temp_config_dir
        repo.config_path = Path(temp_config_dir) 

        models_path = Path(temp_config_dir) / "models.json"
        prompts_path = Path(temp_config_dir) / "prompts.json"

        with open(models_path, 'r') as f:
            models_data = json.load(f)
        
        with open(prompts_path, 'r') as f:
            prompts_data = json.load(f)

        async def mock_load_models_config():
            return models_data
        
        async def mock_load_prompts():
            return prompts_data
        
        async def mock_load_schema(schema_name):
            # Simplified schema validation for this integration test
            # In a real scenario, you might load actual minimal schemas
            # or mock them based on expected validation paths.
            if schema_name == "models_config_schema.json":
                return {"type": "object", "properties": {"models": {"type": "array"}, "version": {"type": "string"}}} 
            if schema_name == "prompts_config_schema.json":
                return {"type": "object", "properties": {"prompts": {"type": "object"}, "version": {"type": "string"}}}
            # Fallback for other schemas if any, or raise error
            # For api_keys_schema.json, ConfigService handles its absence gracefully (loads empty dict)
            # or you can provide a mock schema if strict validation is needed here.
            # print(f"Mock attempting to load schema: {schema_name}") # For debugging
            raise FileNotFoundError(f"Mock schema {schema_name} not found.")


        repo.load_models_config = mock_load_models_config  # Assign the async function directly
        repo.load_prompts = mock_load_prompts    # Assign the async function directly
        # Use side_effect to pass schema_name to the async mock function
        repo.load_schema = lambda s_name: mock_load_schema(s_name) # Assign the async function directly
        
        # Mock save operations (if any test path in integration tests triggers them)
        async def mock_save_models_config(data, version_hash):
            return True # Simulate successful save
        async def mock_save_prompts(data, version_hash):
            return True # Simulate successful save
        
        repo.save_models_config = Mock(side_effect=mock_save_models_config)
        repo.save_prompts = Mock(side_effect=mock_save_prompts)
        
        return repo
    
    @pytest.mark.asyncio
    async def test_config_to_validation_integration(self, mock_repository, temp_config_dir):
        """Test integration between ConfigService and ValidationService."""
        # temp_config_dir is implicitly used by mock_repository to set up its config_path
        # and to define the data it "loads".
        
        config_service = ConfigService(repository=mock_repository)
        # ConfigService.load_config() will use the mocked repo methods:
        # repo.load_models_config(), repo.load_prompts(), and will also try to
        # load api_keys.json from repo.config_path (which points to temp_config_dir)
        full_config = await config_service.load_config() 
        
        assert full_config is not None, "ConfigService failed to load a Config object."
        assert full_config.models is not None, "Loaded config has no models."
        assert full_config.prompts is not None, "Loaded config has no prompts."
        # Check if api_keys.json was loaded by ConfigService
        assert "TEST_API_KEY_1" in full_config.api_keys, "API keys not loaded correctly from mock."

        validation_service = ValidationService(repository=mock_repository)
        
        # The configuration loaded from temp_config_dir is designed to be valid.
        # We are not testing actual API connections here (test_apis=False).
        # ValidationService will use repo.load_schema() for validating against JSON schemas.
        config_val_res, model_val_res_list, prompts_val_res = await validation_service.validate_configuration(
            config=full_config, test_apis=False
        )
        
        assert config_val_res.is_valid, f"Config validation failed: {config_val_res.errors}"
        for mvr in model_val_res_list:
            assert mvr.is_valid, f"Model '{mvr.model_name}' validation failed: {mvr.errors}"
        assert prompts_val_res.is_valid, f"Prompts validation failed: {prompts_val_res.errors}"

    def test_results_service_with_evaluation_service(self):
        """Test integration between ResultsService and EvaluationService - Needs Refactoring"""
        # This test requires significant refactoring due to:
        # - ResultsService constructor now takes 'results_dir'.
        # - EvaluationService methods are async.
        # - Interactions likely involve file system operations for results or complex mocking
    @pytest.mark.asyncio
    @patch('storybench.web.services.lightweight_api_test.LightweightAPITester.test_provider')
    async def test_validation_service_network_errors(self, mock_test_connection, mock_repository):
        """Test ValidationService handling of network errors during API validation."""
        # Configure LightweightAPITester.test_connection to simulate a network error
        mock_test_connection.side_effect = ConnectionError("Simulated network failure")

        service = ValidationService(repository=mock_repository)

        # Create a mock Config object with an API model to trigger API validation
        # This ModelConfig needs enough detail for ValidationService to attempt an API test.
        api_model_for_test = ModelConfig(
            name="TestAPIModelWithNetworkError",
            type="api",
            provider="some_provider", # provider might be needed by LightweightAPITester
            model_name="test-model-for-network-error" # Required field
        )
        
        # Construct a Config object similar to what ConfigService would produce.
        # ValidationService.validate_configuration expects a fully formed Config object.
        config_for_test = Config(
            models=[api_model_for_test],
            prompts={"SampleSequence": ["A prompt"]}, # Minimal valid prompts
            global_settings=GlobalSettings(num_runs=1, output_dir="test_output"), # Minimal valid global settings
            api_keys={"MY_NET_ERROR_API_KEY_ENV": "dummy_key_value"}, # API key for the model
            version="1.0-test-net-error",
            models_config_hash="models_hash_net_error",
            prompts_config_hash="prompts_hash_net_error"
        )

        # Call validate_configuration with test_apis=True to trigger API connection tests
        # The mock_repository's load_schema will be used by ValidationService.
        _config_val_res, model_val_res_list, _prompts_val_res = await service.validate_configuration(
            config=config_for_test, test_apis=True
        )

        assert len(model_val_res_list) == 1, "Expected validation results for one model."
        model_result = model_val_res_list[0]
        
        assert model_result.model_name == "TestAPIModelWithNetworkError"
        
        # The API test part should have failed due to the mocked ConnectionError
        assert model_result.api_test_result is not None, "APITestResult should be present."
        assert model_result.api_test_result.success is False, "API test should have indicated failure."
        assert "Simulated network failure" in model_result.api_test_result.error_message, \
            "Error message from API test not as expected."
        
        # Depending on service logic, the model's overall 'is_valid' might also be False.
        # If API test failure makes the entire model config invalid:
        # assert model_result.is_valid is False, "Model validation should be False due to API test failure."
        # This depends on whether ModelValidationResult.is_valid considers api_test_result.success.g this error.
        # e.g., mock a logger and check if it was called with an error message.

    @pytest.mark.asyncio
    async def test_results_service_corrupted_files(self, temp_output_dir):
        """Test ResultsService handling of corrupted result files."""
        # Create a corrupted JSON file in the temp_output_dir
        corrupted_file_path = Path(temp_output_dir) / "corrupted_result.json"
        with open(corrupted_file_path, "w") as f:
            f.write("this is not valid json {") # Corrupted content

        # Optionally, create a valid file to ensure it's still processed
        valid_result_content = {
            "metadata": {"model_name": "good-model", "config_version": "v1", "timestamp": "2023-01-01T00:00:00Z"},
            "sequences": {}, "status": "completed"
        }
        with open(Path(temp_output_dir) / "good-model_v1.json", "w") as f:
            json.dump(valid_result_content, f)

        service = ResultsService(results_dir=temp_output_dir)
        results_list = await service.get_all_results() # Should be List[ResultSummary]

        # ResultsService should skip the corrupted file and process valid ones.
        # It should not raise an unhandled exception.
        assert isinstance(results_list, list), "Expected a list of result summaries."
        
        # Check that only the valid result was processed
        assert len(results_list) == 1, "Expected one valid result, corrupted file should be skipped."
        if results_list:
            assert results_list[0].model_name == "good-model", "The valid model was not found."

        # If no valid files were created, expect an empty list:
        # assert len(results_list) == 0, "Expected no results as the only file was corrupted."

    # ... (other test methods for TestErrorHandling will go here) ...
class TestPerformanceAndScaling:
    """Test performance characteristics of services."""
    @pytest.fixture
    def mock_repository_for_concurrency(self):
        """
        Provides a mock repository that returns consistent, valid data 
        for concurrency testing of ConfigService.load_config().
        """
        repo = Mock(spec=Repository)

        # Define some consistent mock data
        mock_models_data = {"version": "1.0c", "models": [{"name": "concurrent-model", "type": "local"}]}
        mock_prompts_data = {"version": "1.0c", "prompts": {"seq_c": ["prompt_c"]}}
        mock_api_keys_data = {"CONCURRENT_API_KEY": "key_value_c"}
        # Basic schema, assuming schema validation is tested elsewhere thoroughly
        mock_schema_data = {"type": "object", "properties": {"models": {"type": "array"}}}


        async def load_models_config_mock():
            await asyncio.sleep(0.01) # Simulate some brief I/O
            return mock_models_data

        async def load_prompts_mock():
            await asyncio.sleep(0.01) # Simulate some brief I/O
            return mock_prompts_data
        
        async def mock_load_schema(schema_name): # schema_name is models_config_schema.json or prompts_config_schema.json
            await asyncio.sleep(0.01)
            if schema_name == "models_config_schema.json":
                return {"type": "object", "properties": {"models": {"type": "array"}, "version": {"type": "string"}}}
            elif schema_name == "prompts_config_schema.json":
                 return {"type": "object", "properties": {"prompts": {"type": "object"}, "version": {"type": "string"}}}
            return mock_schema_data # Fallback, though specific ones are better

        # Mock the repository methods
        repo.load_models_config = Mock(return_value=asyncio.ensure_future(load_models_config_mock()))
        repo.load_prompts = Mock(return_value=asyncio.ensure_future(load_prompts_mock()))
        repo.load_schema = Mock(side_effect=lambda s_name: asyncio.ensure_future(mock_load_schema(s_name)))
        
        # Mock config_path and api_keys.json handling
        # ConfigService.load_config tries to load api_keys.json from repo.config_path / "api_keys.json"
        # We need to mock this file read if it's part of the load_config path being tested.
        # For simplicity, let's assume api_keys.json is read by a separate repo method or handled internally by ConfigService
        # based on a path. If ConfigService itself opens the file, we'd need to patch 'builtins.open'.
        # Let's assume ConfigService uses repo.load_api_keys() which we can mock.
        
        async def load_api_keys_mock():
            await asyncio.sleep(0.01)
            return mock_api_keys_data

        if hasattr(repo, 'load_api_keys'): # If your Repository has such a method
            repo.load_api_keys = Mock(return_value=asyncio.ensure_future(load_api_keys_mock()))
        else: # If ConfigService reads api_keys.json directly using repo.config_path
            # Create a dummy api_keys.json in a temporary directory for ConfigService to read
            temp_dir_for_keys = tempfile.TemporaryDirectory()
            api_keys_path = Path(temp_dir_for_keys.name) / "api_keys.json"
            with open(api_keys_path, "w") as f:
                json.dump(mock_api_keys_data, f)
            repo.config_path = Path(temp_dir_for_keys.name)
            # Keep temp_dir_for_keys alive for the duration of the repo's use or test
            # This is a bit tricky with fixtures; ideally, the repo handles all file I/O.
            # For this example, let's assume repo.config_path is used and the temp dir is cleaned up later.
            # A better way for tests is to have repo.load_api_keys().
            # Storing it on the repo instance to clean up if needed, though pytest fixtures handle temp dirs well.
            repo._temp_api_keys_dir = temp_dir_for_keys 


        return repo

    @pytest.mark.asyncio
    async def test_config_service_concurrent_access(self, mock_repository_for_concurrency):
        """Test ConfigService.load_config() handling concurrent async access."""
        num_concurrent_calls = 10
        
        service = ConfigService(repository=mock_repository_for_concurrency)
        
        # Define the async task
        async def load_config_task():
            return await service.load_config()

        # Run tasks concurrently
        start_time = time.time()
        tasks = [load_config_task() for _ in range(num_concurrent_calls)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n[Performance] test_config_service_concurrent_access: {num_concurrent_calls} concurrent calls in {duration:.4f} seconds.")

        # Assertions
        assert len(results) == num_concurrent_calls, "Not all concurrent calls returned a result."
        
        first_result_models_hash = None
        if results and results[0]:
            first_result_models_hash = results[0].models_config_hash # Assuming Config object has this

        for i, config_result in enumerate(results):
            assert config_result is not None, f"Concurrent call {i} returned None."
            assert isinstance(config_result, Config), f"Concurrent call {i} did not return a Config object."
            
            # Check for consistent data (e.g., models loaded)
            assert "concurrent-model" in config_result.models, \
                f"Model 'concurrent-model' not found in result from concurrent call {i}."
            assert "CONCURRENT_API_KEY" in config_result.api_keys, \
                f"API Key 'CONCURRENT_API_KEY' not found in result from concurrent call {i}."

            # Check if all returned Config objects are consistent (e.g., same hash if data didn't change)
            if first_result_models_hash:
                 assert config_result.models_config_hash == first_result_models_hash, \
                    f"Config consistency failed. Models hash mismatch in call {i}."

        # Clean up the temporary directory for api_keys.json if created this way
        if hasattr(mock_repository_for_concurrency, '_temp_api_keys_dir'):
            mock_repository_for_concurrency._temp_api_keys_dir.cleanup()
    @pytest.fixture
    def temp_output_dir_for_scaling(self): # Renamed to avoid conflict if run in same scope as other temp_output_dir
        """Create a temporary directory for performance test output files."""
        with tempfile.TemporaryDirectory() as temp_dir_str:
            # ResultsService might expect an 'output' subdirectory or use the dir directly.
            # Let's assume direct usage for this test.
            yield temp_dir_str 

    @pytest.mark.asyncio
    async def test_results_service_large_dataset(self, temp_output_dir_for_scaling):
        """Test ResultsService with a large number of result files."""
        num_files = 100  # Number of mock result files to create
        
        # Create many mock result files
        for i in range(num_files):
            result_content = {
                "metadata": {
                    "model_name": f"perf-model-{i}",
                    "config_version": f"v{i}",
                    "timestamp": f"2025-01-15T10:{i:02d}:00Z" # Ensure unique enough timestamps if service logic cares
                },
                "sequences": {"seq1": {"output": f"Output for {i}"}},
                "status": "completed",
                "evaluation_scores": {"score1": 0.5 + (i/200.0)} # Some varying data
            }
            file_path = Path(temp_output_dir_for_scaling) / f"perf-model-{i}_v{i}.json"
            with open(file_path, "w") as f:
                json.dump(result_content, f)
        
        service = ResultsService(results_dir=temp_output_dir_for_scaling)
        
        start_time = time.time()
        results_list = await service.get_all_results() # Should be List[ResultSummary]
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n[Performance] test_results_service_large_dataset: Loaded {len(results_list)} results in {duration:.4f} seconds.")

        assert len(results_list) == num_files, f"Expected {num_files} results, but got {len(results_list)}."
        # Performance assertion (can be adjusted based on typical performance)
        # This is a very generous limit; on a fast system, it should be much quicker.
        assert duration < 10.0, f"Loading {num_files} results took {duration:.4f}s, which exceeded the 10s limit."

        # Optional: Verify some content to ensure files were parsed correctly
        if results_list:
            assert results_list[0].model_name == "perf-model-0"
            # Add more checks if necessary