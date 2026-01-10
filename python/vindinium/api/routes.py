"""FastAPI routes for game API."""

from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import secrets

from vindinium.models import Game, Dir
from vindinium.system.generator import Generator
from vindinium.system.map_parser import MapParser
from vindinium.game_logic.arbiter import Arbiter
from vindinium.db.repositories import GameRepository, get_game_repository


router = APIRouter(prefix="/api", tags=["game"])


# Request/Response Models
class TrainingRequest(BaseModel):
    """Training game creation request."""
    key: str = Field(..., description="API key for authentication")
    turns: Optional[int] = Field(300, ge=1, le=1000, description="Maximum number of turns")
    map: Optional[str] = Field(None, description="Map name (m1-m6) or random")


class MoveResponse(BaseModel):
    """Response after processing a move."""
    game: dict
    hero: dict
    token: str
    viewUrl: str
    playUrl: str


@router.post("/training")
async def create_training_game(
    key: str = Form(...),
    turns: Optional[int] = Form(300),
    map: Optional[str] = Form(None),
    repo: GameRepository = Depends(get_game_repository),
) -> JSONResponse:
    """
    Create a new training game.
    
    Args:
        key: API key (not validated in training mode)
        turns: Maximum number of turns (default 300)
        map: Map name (m1-m6) or None for random
        
    Returns:
        Initial game state with hero token
    """
    # Validate turns
    if turns < 1 or turns > 1000:
        raise HTTPException(status_code=400, detail="Turns must be between 1 and 1000")
    
    # Generate game ID
    game_id = f"training-{secrets.token_hex(8)}"
    
    # Create board
    if map and map.startswith("m") and map[1:].isdigit():
        # Use default map
        board = MapParser.parse_default_map(map)
    else:
        # Generate random map
        board = Generator.create_random_board(size=20)
    
    # Create game state
    game = Generator.create_initial_game_state(
        game_id=game_id,
        board=board,
        max_turns=turns,
        training=True,
    )
    
    # Save to database
    await repo.save(game)
    
    # Get hero 1 (the player in training mode)
    hero = game.hero1
    
    # Build response
    response_data = {
        "game": game.to_dict(),
        "hero": hero.to_dict(),
        "token": hero.token,
        "viewUrl": f"/game/{game_id}",
        "playUrl": f"/api/{game_id}/{hero.token}",
    }
    
    return JSONResponse(content=response_data)


@router.post("/{game_id}/{token}/{direction}")
async def process_move(
    game_id: str,
    token: str,
    direction: str,
    repo: GameRepository = Depends(get_game_repository),
) -> JSONResponse:
    """
    Process a hero's move in a game.
    
    Args:
        game_id: Unique game identifier
        token: Hero's authentication token
        direction: Move direction (North, South, East, West, Stay)
        
    Returns:
        Updated game state after move
    """
    # Get game from database
    game = await repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check if game is finished
    if game.finished:
        raise HTTPException(status_code=400, detail="Game is already finished")
    
    # Find hero by token
    hero = game.get_hero_by_token(token)
    if hero is None:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    # Check if it's this hero's turn
    if game.hero_id != hero.id:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Parse direction
    try:
        dir_enum = Dir(direction)
    except ValueError:
        # Invalid direction defaults to Stay
        dir_enum = Dir.STAY
    
    # Process the move
    game = Arbiter.process_move(game, hero.id, dir_enum)
    
    # Advance to next turn
    game = game.step()
    
    # Save updated game state
    await repo.save(game)
    
    # Build response
    updated_hero = game.get_hero(hero.id)
    response_data = {
        "game": game.to_dict(),
        "hero": updated_hero.to_dict() if updated_hero else hero.to_dict(),
        "token": token,
        "viewUrl": f"/game/{game_id}",
        "playUrl": f"/api/{game_id}/{token}",
    }
    
    return JSONResponse(content=response_data)


@router.get("/game/{game_id}")
async def get_game_state(
    game_id: str,
    repo: GameRepository = Depends(get_game_repository),
) -> JSONResponse:
    """
    Get the current state of a game.
    
    Args:
        game_id: Unique game identifier
        
    Returns:
        Current game state
    """
    game = await repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return JSONResponse(content={"game": game.to_dict()})
