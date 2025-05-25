"""MongoDB connection management with retry logic and health checks."""

import asyncio
import logging
from typing import Optional
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages MongoDB Atlas connection with retry logic and health checks."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._connection_string: Optional[str] = None
        self._database_name: Optional[str] = None
        
    async def connect(self, connection_string: str, database_name: str = "storybench") -> AsyncIOMotorDatabase:
        """
        Establish connection to MongoDB Atlas with retry logic.
        
        Args:
            connection_string: MongoDB Atlas connection string
            database_name: Database name to connect to
            
        Returns:
            AsyncIOMotorDatabase instance
            
        Raises:
            ConnectionFailure: If unable to connect after retries
        """
        self._connection_string = connection_string
        self._database_name = database_name
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{max_retries})")
                
                # Create client with connection pool settings
                self.client = AsyncIOMotorClient(
                    connection_string,
                    maxPoolSize=10,
                    minPoolSize=1,
                    maxIdleTimeMS=45000,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                )
                
                # Test the connection
                await self.client.admin.command('ping')
                
                # Get database
                self.database = self.client[database_name]
                
                logger.info(f"Successfully connected to MongoDB database: {database_name}")
                return self.database
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed to connect to MongoDB after all retries")
                    raise ConnectionFailure(f"Unable to connect to MongoDB: {e}")
                    
    async def disconnect(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            logger.info("Disconnected from MongoDB")
            
    async def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self.client or not self.database:
                return False
                
            # Simple ping to check connection
            await self.client.admin.command('ping')
            return True
            
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False
            
    async def ensure_connection(self):
        """Ensure database connection is active, reconnect if necessary."""
        if not await self.health_check():
            if self._connection_string and self._database_name:
                logger.info("Reconnecting to database...")
                await self.connect(self._connection_string, self._database_name)
            else:
                raise ConnectionError("Cannot reconnect: connection parameters not available")

# Global connection instance
_db_connection = DatabaseConnection()

async def init_database(connection_string: str = None, database_name: str = "storybench") -> AsyncIOMotorDatabase:
    """
    Initialize database connection.
    
    Args:
        connection_string: MongoDB connection string (gets from env if not provided)
        database_name: Database name
        
    Returns:
        AsyncIOMotorDatabase instance
    """
    if connection_string is None:
        # Determine if we're in test mode
        if os.getenv("PYTEST_CURRENT_TEST") or database_name.endswith("_test"):
            connection_string = os.getenv("MONGODB_TEST_URI")
            if not connection_string:
                connection_string = os.getenv("MONGODB_URI")
                if connection_string and "storybench?" in connection_string:
                    connection_string = connection_string.replace("storybench?", "storybench_test?")
        else:
            connection_string = os.getenv("MONGODB_URI")
            
        if not connection_string:
            raise ValueError("MongoDB connection string not found in environment variables")
    
    return await _db_connection.connect(connection_string, database_name)

async def get_database() -> AsyncIOMotorDatabase:
    """
    Get the current database instance.
    
    Returns:
        AsyncIOMotorDatabase instance
        
    Raises:
        ConnectionError: If database is not initialized
    """
    if _db_connection.database is None:
        raise ConnectionError("Database not initialized. Call init_database() first.")
    
    # Ensure connection is still healthy
    await _db_connection.ensure_connection()
    return _db_connection.database

async def close_database():
    """Close the database connection."""
    await _db_connection.disconnect()

@asynccontextmanager
async def get_database_context(connection_string: str = None, database_name: str = "storybench"):
    """
    Context manager for database connections.
    
    Args:
        connection_string: MongoDB connection string
        database_name: Database name
        
    Yields:
        AsyncIOMotorDatabase instance
    """
    db = await init_database(connection_string, database_name)
    try:
        yield db
    finally:
        await close_database()
