"""Test database config service."""

import pytest
from unittest.mock import Mock, AsyncMock
import hashlib
import json

from src.storybench.database.services.config_service import ConfigService


class TestConfigService:
    """Test ConfigService functionality."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        return Mock()
    
    @pytest.fixture
    def config_service(self, mock_database):
        """Create ConfigService with mocked dependencies."""
        with pytest.MonkeyPatch().context() as m:
            # Mock the repository classes
            mock_model_repo = Mock()
            mock_prompt_repo = Mock()
            mock_criteria_repo = Mock()
            
            m.setattr('src.storybench.database.services.config_service.ModelRepository', 
                     lambda db: mock_model_repo)
            m.setattr('src.storybench.database.services.config_service.PromptRepository', 
                     lambda db: mock_prompt_repo)
            m.setattr('src.storybench.database.services.config_service.CriteriaRepository', 
                     lambda db: mock_criteria_repo)
            
            service = ConfigService(mock_database)
            service.model_repo = mock_model_repo
            service.prompt_repo = mock_prompt_repo
            service.criteria_repo = mock_criteria_repo
            
            return service
    
    def test_initialization(self, mock_database):
        """Test ConfigService initialization."""
        with pytest.MonkeyPatch().context() as m:
            mock_model_repo = Mock()
            mock_prompt_repo = Mock()
            mock_criteria_repo = Mock()
            
            m.setattr('src.storybench.database.services.config_service.ModelRepository', 
                     lambda db: mock_model_repo)
            m.setattr('src.storybench.database.services.config_service.PromptRepository', 
                     lambda db: mock_prompt_repo)
            m.setattr('src.storybench.database.services.config_service.CriteriaRepository', 
                     lambda db: mock_criteria_repo)
            
            service = ConfigService(mock_database)
            
            assert service.database == mock_database

    def test_generate_config_hash(self, config_service):
        """Test configuration hash generation."""
        config_data = {
            "models": ["gpt-4", "claude-3"],
            "prompts": ["creative_writing"],
            "temperature": 0.9
        }
        
        hash_result = config_service.generate_config_hash(config_data)
        
        # Verify hash format and consistency
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16
        
        # Verify hash is deterministic
        hash_result2 = config_service.generate_config_hash(config_data)
        assert hash_result == hash_result2
    
    def test_generate_config_hash_different_order(self, config_service):
        """Test that hash is consistent regardless of key order."""
        config1 = {"a": 1, "b": 2, "c": 3}
        config2 = {"c": 3, "a": 1, "b": 2}
        
        hash1 = config_service.generate_config_hash(config1)
        hash2 = config_service.generate_config_hash(config2)
        
        assert hash1 == hash2
    
    def test_generate_config_hash_different_data(self, config_service):
        """Test that different data produces different hashes."""
        config1 = {"models": ["gpt-4"]}
        config2 = {"models": ["claude-3"]}
        
        hash1 = config_service.generate_config_hash(config1)
        hash2 = config_service.generate_config_hash(config2)
        
        assert hash1 != hash2
    
    @pytest.mark.asyncio
    async def test_get_active_models(self, config_service):
        """Test getting active models configuration."""
        expected_models = Mock()
        config_service.model_repo.find_active = AsyncMock(return_value=expected_models)
        
        result = await config_service.get_active_models()
        
        assert result == expected_models
        config_service.model_repo.find_active.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_prompts(self, config_service):
        """Test getting active prompts configuration."""
        expected_prompts = Mock()
        config_service.prompt_repo.find_active = AsyncMock(return_value=expected_prompts)
        
        result = await config_service.get_active_prompts()
        
        assert result == expected_prompts
        config_service.prompt_repo.find_active.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_criteria(self, config_service):
        """Test getting active criteria configuration."""
        expected_criteria = Mock()
        config_service.criteria_repo.find_active = AsyncMock(return_value=expected_criteria)
        
        result = await config_service.get_active_criteria()
        
        assert result == expected_criteria
        config_service.criteria_repo.find_active.assert_called_once()
