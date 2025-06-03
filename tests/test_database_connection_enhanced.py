"""Enhanced database connection tests for coverage boost."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storybench.database.connection import DatabaseConnection


class TestDatabaseConnectionEnhanced:
    """Enhanced DatabaseConnection tests."""
    
    def test_database_connection_initialization(self):
        """Test DatabaseConnection initialization."""
        connection_string = "postgresql://user:pass@localhost:5432/testdb"
        db = DatabaseConnection()
        
        # Test default initialization
        assert db.pool is None
        
    def test_database_connection_string_property(self):
        """Test connection string property."""
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
            db = DatabaseConnection()
            assert 'postgresql://' in db.connection_string
            
    def test_database_connection_mongodb_fallback(self):
        """Test MongoDB connection fallback.""" 
        with patch.dict('os.environ', {'MONGODB_URL': 'mongodb://localhost:27017/testdb'}):
            db = DatabaseConnection()
            assert 'mongodb://' in db.connection_string
            
    @patch('storybench.database.connection.asyncpg')
    async def test_connect_postgresql_success(self, mock_asyncpg):
        """Test successful PostgreSQL connection."""
        mock_pool = Mock()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
            db = DatabaseConnection()
            await db.connect()
            
            assert db.pool == mock_pool
            mock_asyncpg.create_pool.assert_called_once()
            
    @patch('storybench.database.connection.AsyncIOMotorClient')
    async def test_connect_mongodb_success(self, mock_motor_client):
        """Test successful MongoDB connection."""
        mock_client = Mock()
        mock_db = Mock()
        mock_motor_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        
        with patch.dict('os.environ', {'MONGODB_URL': 'mongodb://localhost:27017/testdb'}):
            db = DatabaseConnection()
            await db.connect()
            
            assert db.client == mock_client
            assert db.db == mock_db
            
    @patch('storybench.database.connection.asyncpg')
    async def test_connect_postgresql_failure(self, mock_asyncpg):
        """Test PostgreSQL connection failure."""
        mock_asyncpg.create_pool = AsyncMock(side_effect=Exception("Connection failed"))
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://invalid'}):
            db = DatabaseConnection()
            
            with pytest.raises(Exception, match="Connection failed"):
                await db.connect()
                
    @patch('storybench.database.connection.AsyncIOMotorClient')
    async def test_connect_mongodb_failure(self, mock_motor_client):
        """Test MongoDB connection failure."""
        mock_motor_client.side_effect = Exception("MongoDB connection failed")
        
        with patch.dict('os.environ', {'MONGODB_URL': 'mongodb://invalid'}):
            db = DatabaseConnection()
            
            with pytest.raises(Exception, match="MongoDB connection failed"):
                await db.connect()
            
    @patch('storybench.database.connection.asyncpg')
    async def test_disconnect_postgresql(self, mock_asyncpg):
        """Test PostgreSQL disconnection."""
        mock_pool = Mock()
        mock_pool.close = AsyncMock()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
            db = DatabaseConnection()
            await db.connect()
            await db.disconnect()
            
            mock_pool.close.assert_called_once()
            assert db.pool is None
            
    @patch('storybench.database.connection.AsyncIOMotorClient')
    async def test_disconnect_mongodb(self, mock_motor_client):
        """Test MongoDB disconnection."""
        mock_client = Mock()
        mock_client.close = AsyncMock()
        mock_motor_client.return_value = mock_client
        mock_client.__getitem__.return_value = Mock()
        
        with patch.dict('os.environ', {'MONGODB_URL': 'mongodb://test'}):
            db = DatabaseConnection()
            await db.connect()
            await db.disconnect()
            
            mock_client.close.assert_called_once()
            assert db.client is None
            assert db.db is None
            
    async def test_disconnect_without_connection(self):
        """Test disconnect when not connected."""
        db = DatabaseConnection()
        
        # Should not raise an error
        await db.disconnect()
        
        assert db.pool is None
        assert db.client is None
        
    @patch('storybench.database.connection.asyncpg')
    async def test_execute_query_postgresql(self, mock_asyncpg):
        """Test query execution on PostgreSQL."""
        mock_pool = Mock()
        mock_connection = Mock()
        mock_connection.fetch = AsyncMock(return_value=[{"id": 1, "name": "test"}])
        mock_pool.acquire = AsyncMock(return_value=mock_connection)
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
            db = DatabaseConnection()
            await db.connect()
            
            result = await db.execute_query("SELECT * FROM test")
            
            assert result == [{"id": 1, "name": "test"}]
            mock_connection.fetch.assert_called_once_with("SELECT * FROM test")
            
    def test_is_connected_postgresql(self):
        """Test connection status check for PostgreSQL."""
        db = DatabaseConnection()
        
        assert not db.is_connected()
        
        db.pool = Mock()
        assert db.is_connected()
        
    def test_is_connected_mongodb(self):
        """Test connection status check for MongoDB."""
        db = DatabaseConnection()
        
        assert not db.is_connected()
        
        db.client = Mock()
        assert db.is_connected()
