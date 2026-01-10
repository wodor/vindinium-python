"""Repository for game persistence."""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from vindinium.models import Game
from vindinium.db.mongodb import get_db


class GameRepository:
    """Repository for managing game state in MongoDB."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with database connection."""
        self.db = db
        self.collection = db.games
    
    async def create_indexes(self) -> None:
        """Create database indexes for efficient querying."""
        # Index on game ID for fast lookups
        await self.collection.create_index("id", unique=True)
        # Index on status for filtering active games
        await self.collection.create_index("status")
        # Index on training flag for filtering game types
        await self.collection.create_index("training")
    
    async def save(self, game: Game) -> str:
        """Save or update a game in the database.
        
        Args:
            game: Game instance to save
            
        Returns:
            Game ID
        """
        game_dict = game.to_dict()
        
        # Upsert: update if exists, insert if new
        await self.collection.update_one(
            {"id": game.id},
            {"$set": game_dict},
            upsert=True
        )
        
        return game.id
    
    async def get(self, game_id: str) -> Optional[Game]:
        """Retrieve a game by ID.
        
        Args:
            game_id: Unique game identifier
            
        Returns:
            Game instance or None if not found
        """
        game_dict = await self.collection.find_one({"id": game_id})
        
        if game_dict is None:
            return None
        
        # Remove MongoDB's _id field
        game_dict.pop("_id", None)
        
        return Game.from_dict(game_dict)
    
    async def delete(self, game_id: str) -> bool:
        """Delete a game from the database.
        
        Args:
            game_id: Unique game identifier
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"id": game_id})
        return result.deleted_count > 0
    
    async def list_active(self, limit: int = 100) -> list[Game]:
        """List active (non-finished) games.
        
        Args:
            limit: Maximum number of games to return
            
        Returns:
            List of active Game instances
        """
        cursor = self.collection.find(
            {"status": {"$in": ["Created", "Started"]}}
        ).limit(limit)
        
        games = []
        async for game_dict in cursor:
            game_dict.pop("_id", None)
            games.append(Game.from_dict(game_dict))
        
        return games


async def get_game_repository() -> GameRepository:
    """Dependency injection for FastAPI routes to get repository instance."""
    db = await get_db()
    return GameRepository(db)
