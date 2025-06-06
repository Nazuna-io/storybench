"""Test database connection and basic functionality."""

import pytest
import os
from unittest.mock import AsyncMock, patch
from pymongo.errors import ConnectionFailure

from src.storybench.database.connection import DatabaseConnection

class TestDatabaseConnection:
    """Test database connection functionality."""
    
    @pytest.mark.asyncio
    async def test_database_connection_init(self):
        """Test database connection initialization."""
        db_conn = DatabaseConnection()
        assert db_conn.client is None
        assert db_conn.database is None
        assert db_conn._connection_string is None
        assert db_conn._database_name is None
            
    @pytest.mark.asyncio
    async def test_database_connection_health_check(self):
        """Test database health check."""
        db_conn = DatabaseConnection()
        
        # Test when no connection exists
        health = await db_conn.health_check()
        assert health is False
        
    @pytest.mark.asyncio
    async def test_connect_with_mocked_client(self):
        """Test successful database connection with mocked client."""
        db_conn = DatabaseConnection()
        
        with patch('src.storybench.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client_class.return_value = mock_client
            
            db = await db_conn.connect("mongodb://test:test@localhost/test", "test_db")
            
            assert db_conn.client is not None
            assert db_conn.database is not None
            assert db_conn._connection_string == "mongodb://test:test@localhost/test"
            assert db_conn._database_name == "test_db"
            
            mock_client.admin.command.assert_called_once_with('ping')
    
    @pytest.mark.asyncio
    async def test_connect_failure_retry_logic(self):
        """Test connection failure and retry logic."""
        db_conn = DatabaseConnection()
        
        with patch('src.storybench.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(side_effect=ConnectionFailure("Connection failed"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ConnectionFailure):
                await db_conn.connect("mongodb://test:test@localhost/test", "test_db")
            
            # Should have tried 3 times (max_retries)
            assert mock_client.admin.command.call_count == 3
    
    @pytest.mark.asyncio
    async def test_health_check_with_connection(self):
        """Test health check with active connection."""
        db_conn = DatabaseConnection()
        
        with patch('src.storybench.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client_class.return_value = mock_client
            
            await db_conn.connect("mongodb://test@localhost/test", "test_db")
            
            # Health check should pass with active connection
            health = await db_conn.health_check()
            assert health is True
    
    @pytest.mark.asyncio
    async def test_health_check_connection_failure(self):
        """Test health check when connection fails."""
        db_conn = DatabaseConnection()
        
        with patch('src.storybench.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client_class.return_value = mock_client
            
            await db_conn.connect("mongodb://test@localhost/test", "test_db")
            
            # Simulate health check failure
            mock_client.admin.command = AsyncMock(side_effect=ConnectionFailure("Connection failed"))
            
            health = await db_conn.health_check()
            assert health is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test database disconnection."""
        db_conn = DatabaseConnection()
        
        with patch('src.storybench.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            await db_conn.connect("mongodb://test@localhost/test", "test_db")
            await db_conn.disconnect()
            
            assert db_conn.client is None
            assert db_conn.database is None
            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_without_connection(self):
        """Test disconnection when no connection exists."""
        db_conn = DatabaseConnection()
        
        # Should not raise an error
        await db_conn.disconnect()
        assert db_conn.client is None
        assert db_conn.database is None
    
    @pytest.mark.asyncio
    async def test_connection_string_sanitization(self):
        """Test that connection string sanitization works."""
        db_conn = DatabaseConnection()
        
        with patch('src.storybench.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.admin.command = AsyncMock(return_value={'ok': 1})
            mock_client_class.return_value = mock_client
            
            with patch('src.storybench.database.connection.logger') as mock_logger:
                await db_conn.connect("mongodb://user:password@localhost/test", "test_db")
                
                # Verify that password is sanitized in logs
                calls = mock_logger.info.call_args_list
                log_messages = [call[0][0] for call in calls]
                
                # Should contain sanitized connection string
                assert any("user:***@localhost" in msg for msg in log_messages)
                # Should not contain actual password
                assert not any("password" in msg for msg in log_messages)
