"""Test configuration migration and management."""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch

from storybench.database.migrations.config_migration import ConfigMigrationService
from storybench.database.services.config_service import ConfigService

class TestConfigMigration:
    """Test configuration migration functionality."""
    
    @pytest.mark.asyncio
    async def test_config_service_hash_generation(self):
        """Test configuration hash generation."""
        mock_db = AsyncMock()
        config_service = ConfigService(mock_db)
        
        test_config = {"test": "data", "numbers": [1, 2, 3]}
        hash1 = config_service.generate_config_hash(test_config)
        hash2 = config_service.generate_config_hash(test_config)
        
        # Same config should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Should be 16 characters as specified
        
        # Different config should generate different hash
        different_config = {"test": "different", "numbers": [1, 2, 3]}
        hash3 = config_service.generate_config_hash(different_config)
        assert hash1 != hash3
        
    @pytest.mark.asyncio
    async def test_migration_service_initialization(self):
        """Test migration service initialization."""
        mock_db = AsyncMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            migration_service = ConfigMigrationService(mock_db, temp_dir)
            
            assert migration_service.database == mock_db
            assert migration_service.config_dir == Path(temp_dir)
            assert isinstance(migration_service.config_service, ConfigService)
