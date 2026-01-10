"""MongoDB connection and client management."""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from vindinium.config import settings


class MongoDBClient:
    """MongoDB client singleton for managing database connections."""
    
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """Connect to MongoDB using settings from config."""
        if cls._client is None:
            cls._client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
            )
            cls._db = cls._client[settings.database_name]
            # Verify connection
            await cls._client.admin.command('ping')
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close the MongoDB connection."""
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get the database instance.
        
        Raises:
            RuntimeError: If not connected to database.
        """
        if cls._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls._db
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """Get the MongoDB client instance.
        
        Raises:
            RuntimeError: If not connected to database.
        """
        if cls._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls._client


async def get_db() -> AsyncIOMotorDatabase:
    """Dependency injection for FastAPI routes to get database instance."""
    return MongoDBClient.get_database()
