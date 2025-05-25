"""Test database connection and basic functionality."""

import pytest
import os
from unittest.mock import AsyncMock, patch

from storybench.database.connection import (
    init_database, 
    get_database, 
    close_database,
    DatabaseConnection
)

class TestDatabaseConnection:
    """Test database connection functionality."""
    
    @pytest.mark.asyncio
    async def test_database_connection_init(self):
        """Test database initialization."""
        # Mock the MongoDB connection
        with patch('storybench.database.connection.AsyncIOMotorClient') as mock_client:
            mock_client.return_value.admin.command = AsyncMock()
            
            # Test with explicit connection string
            db = await init_database("mongodb://test", "test_db")
            assert db is not None
            
    @pytest.mark.asyncio 
    async def test_database_connection_health_check(self):
        """Test database health check."""
        db_conn = DatabaseConnection()
        
        # Test when no connection exists
        health = await db_conn.health_check()
        assert health is False
        
    @pytest.mark.asyncio
    async def test_get_database_without_init(self):
        """Test getting database without initialization raises error."""
        # Clear any existing connection
        from storybench.database.connection import _db_connection
        await _db_connection.disconnect()
        
        with pytest.raises(ConnectionError):
            await get_database()
