"""Database connection tests for coverage boost."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.database.connection import DatabaseConnection


class TestDatabaseConnection:
    """Comprehensive DatabaseConnection tests."""
    
    def test_database_connection_init(self):
        """Test DatabaseConnection initialization."""
        connection_string = "postgresql://user:pass@localhost:5432/testdb"
        db = DatabaseConnection(connection_string)
        
        assert db.connection_string == connection_string
        assert db.pool is None
        
    def test_database_connection_with_ssl(self):
        """Test DatabaseConnection with SSL parameters."""
        connection_string = "postgresql://user:pass@localhost:5432/testdb?sslmode=require"
        db = DatabaseConnection(connection_string)
        
        assert "sslmode=require" in db.connection_string
        
    @patch('storybench.database.connection.asyncpg')
    async def test_connect_success(self, mock_asyncpg):
        """Test successful database connection."""
        mock_pool = Mock()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        
        db = DatabaseConnection("postgresql://test")
        await db.connect()
        
        assert db.pool == mock_pool
        mock_asyncpg.create_pool.assert_called_once()
        
    @patch('storybench.database.connection.asyncpg')
    async def test_connect_failure(self, mock_asyncpg):
        """Test database connection failure."""
        mock_asyncpg.create_pool = AsyncMock(side_effect=Exception("Connection failed"))
        
        db = DatabaseConnection("postgresql://invalid")
        
        with pytest.raises(Exception, match="Connection failed"):
            await db.connect()
            
    @patch('storybench.database.connection.asyncpg')
    async def test_disconnect(self, mock_asyncpg):
        """Test database disconnection."""
        mock_pool = Mock()
        mock_pool.close = AsyncMock()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        
        db = DatabaseConnection("postgresql://test")
        await db.connect()
        await db.disconnect()
        
        mock_pool.close.assert_called_once()
        assert db.pool is None
        
    async def test_disconnect_without_connection(self):
        """Test disconnect when not connected."""
        db = DatabaseConnection("postgresql://test")
        
        # Should not raise an error
        await db.disconnect()
        
        assert db.pool is None
        
    @patch('storybench.database.connection.asyncpg')
    async def test_get_connection(self, mock_asyncpg):
        """Test getting connection from pool."""
        mock_pool = Mock()
        mock_connection = Mock()
        mock_pool.acquire = AsyncMock(return_value=mock_connection)
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        
        db = DatabaseConnection("postgresql://test")
        await db.connect()
        
        connection = await db.get_connection()
        
        assert connection == mock_connection
        mock_pool.acquire.assert_called_once()
