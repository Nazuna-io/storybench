"""
Comprehensive tests for database/services/config_service.py
These tests cover the ConfigService with mocked repositories.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import the service we want to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestConfigService:
    """Test the ConfigService class."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database."""
        return Mock()
    
    @patch('storybench.database.services.config_service.ModelRepository')
    @patch('storybench.database.services.config_service.PromptRepository')
    @patch('storybench.database.services.config_service.CriteriaRepository')
    def test_config_service_initialization(self, mock_criteria_repo, mock_prompt_repo, mock_model_repo, mock_database):
        """Test config service initialization."""
        from storybench.database.services.config_service import ConfigService
        
        service = ConfigService(mock_database)
        
        assert service.database == mock_database
        mock_model_repo.assert_called_once_with(mock_database)
        mock_prompt_repo.assert_called_once_with(mock_database)
        mock_criteria_repo.assert_called_once_with(mock_database)
    
    def test_generate_config_hash(self):
        """Test configuration hash generation."""
        from storybench.database.services.config_service import ConfigService
        
        # Create service with minimal mocking just for hash testing
        with patch('storybench.database.services.config_service.ModelRepository'), \
             patch('storybench.database.services.config_service.PromptRepository'), \
             patch('storybench.database.services.config_service.CriteriaRepository'):
            
            service = ConfigService(Mock())
            
            config_data = {
                "models": ["gpt-4", "claude-3"],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # Generate hash
            hash_result = service.generate_config_hash(config_data)
            
            # Verify it's a string of expected length (16 chars from SHA256)
            assert isinstance(hash_result, str)
            assert len(hash_result) == 16
            
            # Verify consistency - same input should produce same hash
            hash_result2 = service.generate_config_hash(config_data)
            assert hash_result == hash_result2
    
    def test_generate_config_hash_order_independence(self):
        """Test that config hash is order-independent."""
        from storybench.database.services.config_service import ConfigService
        
        with patch('storybench.database.services.config_service.ModelRepository'), \
             patch('storybench.database.services.config_service.PromptRepository'), \
             patch('storybench.database.services.config_service.CriteriaRepository'):
            
            service = ConfigService(Mock())
            
            config1 = {"a": 1, "b": 2, "c": 3}
            config2 = {"c": 3, "a": 1, "b": 2}  # Different order
            
            hash1 = service.generate_config_hash(config1)
            hash2 = service.generate_config_hash(config2)
            
            assert hash1 == hash2
    
    @patch('storybench.database.services.config_service.ModelRepository')
    @patch('storybench.database.services.config_service.PromptRepository')
    @patch('storybench.database.services.config_service.CriteriaRepository')
    @pytest.mark.asyncio
    async def test_get_active_models(self, mock_criteria_repo, mock_prompt_repo, mock_model_repo):
        """Test getting active models configuration."""
        from storybench.database.services.config_service import ConfigService
        
        # Setup mock response
        mock_models = Mock()
        mock_models.config_hash = "abc123"
        mock_models.is_active = True
        
        mock_model_instance = AsyncMock()
        mock_model_instance.find_active.return_value = mock_models
        mock_model_repo.return_value = mock_model_instance
        
        service = ConfigService(Mock())
        
        # Execute
        result = await service.get_active_models()
        
        # Verify
        assert result == mock_models
        mock_model_instance.find_active.assert_called_once()
    
    def test_hash_different_values_different_hashes(self):
        """Test that different configs produce different hashes."""
        from storybench.database.services.config_service import ConfigService
        
        with patch('storybench.database.services.config_service.ModelRepository'), \
             patch('storybench.database.services.config_service.PromptRepository'), \
             patch('storybench.database.services.config_service.CriteriaRepository'):
            
            service = ConfigService(Mock())
            
            config1 = {"temperature": 0.7}
            config2 = {"temperature": 0.8}
            
            hash1 = service.generate_config_hash(config1)
            hash2 = service.generate_config_hash(config2)
            
            assert hash1 != hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
