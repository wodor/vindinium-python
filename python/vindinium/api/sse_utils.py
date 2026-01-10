"""Server-Sent Events utilities for game state streaming."""

import asyncio
import json
from typing import AsyncGenerator, Optional
from vindinium.models import Game
from vindinium.db.repositories import GameRepository
from vindinium.api.serializers import serialize_game


async def game_state_stream(
    game_id: str,
    repo: GameRepository,
    poll_interval: float = 1.0,
    max_iterations: int = 1000,
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events for game state updates.
    
    Args:
        game_id: Game identifier to stream
        repo: Game repository for fetching state
        poll_interval: Time in seconds between polls (default 1.0)
        max_iterations: Maximum number of polls before stopping (default 1000)
        
    Yields:
        JSON-serialized game state as SSE data
    """
    iteration = 0
    last_turn = -1
    
    while iteration < max_iterations:
        try:
            # Fetch current game state
            game = await repo.get(game_id)
            
            if game is None:
                # Game not found - send error and stop
                yield json.dumps({"error": "Game not found"})
                break
            
            # Only send updates when turn changes or first iteration
            if game.turn != last_turn or iteration == 0:
                # Send game state update using serializer
                yield json.dumps(serialize_game(game))
                last_turn = game.turn
            
            # Check if game is finished
            if game.finished:
                # Send final state and stop
                break
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            iteration += 1
            
        except asyncio.CancelledError:
            # Client disconnected
            break
        except Exception as e:
            # Log error but continue
            print(f"Error in game state stream: {e}")
            await asyncio.sleep(poll_interval)
            iteration += 1


async def active_games_stream(
    repo: GameRepository,
    poll_interval: float = 2.0,
    max_iterations: int = 500,
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events for active (non-finished) games.
    
    Args:
        repo: Game repository for fetching games
        poll_interval: Time in seconds between polls (default 2.0)
        max_iterations: Maximum number of polls before stopping
        
    Yields:
        JSON-serialized list of active game IDs
    """
    iteration = 0
    
    while iteration < max_iterations:
        try:
            # Fetch active games
            games = await repo.get_active_games(limit=10)
            
            # Send game IDs
            game_ids = [game.id for game in games]
            yield json.dumps({"games": game_ids, "count": len(game_ids)})
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            iteration += 1
            
        except asyncio.CancelledError:
            # Client disconnected
            break
        except Exception as e:
            # Log error but continue
            print(f"Error in active games stream: {e}")
            await asyncio.sleep(poll_interval)
            iteration += 1
