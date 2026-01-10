"""Serializers for game state to match client JSON schema expectations."""

from typing import Any
from vindinium.models import Game, Hero, Board, Tile, TileType


def serialize_hero(hero: Hero) -> dict[str, Any]:
    """
    Serialize a hero to match client expectations.
    
    Client expects:
    {
      "id": 1,
      "name": "Bot Name",
      "pos": {"x": 5, "y": 5},
      "life": 100,
      "gold": 0,
      "mineCount": 0,
      "spawnPos": {"x": 5, "y": 5},
      "crashed": false
    }
    """
    return {
        "id": hero.id,
        "name": hero.name,
        "userId": hero.user_id,
        "elo": hero.elo or 1200,
        "pos": {"x": hero.pos.x, "y": hero.pos.y},
        "life": hero.life,
        "gold": hero.gold,
        "mineCount": hero.mine_count,
        "spawnPos": {"x": hero.spawn_pos.x, "y": hero.spawn_pos.y},
        "crashed": hero.crashed,
    }


def serialize_board_tiles(board: Board) -> str:
    """
    Serialize board tiles to string format expected by client.
    
    Client expects a string where each tile is 2 characters:
    - "  " = Air
    - "##" = Wall
    - "[]" = Tavern
    - "$-" = Neutral Mine
    - "$1", "$2", "$3", "$4" = Owned Mine
    - "@1", "@2", "@3", "@4" = Hero spawn (encoded as Air in tiles string)
    """
    tiles_str = ""
    for tile in board.tiles:
        if tile.type == TileType.AIR:
            tiles_str += "  "
        elif tile.type == TileType.WALL:
            tiles_str += "##"
        elif tile.type == TileType.TAVERN:
            tiles_str += "[]"
        elif tile.type == TileType.MINE:
            if tile.owner is None:
                tiles_str += "$-"
            else:
                tiles_str += f"${tile.owner}"
    return tiles_str


def serialize_board(board: Board) -> dict[str, Any]:
    """
    Serialize a board to match client expectations.
    
    Client expects:
    {
      "size": 20,
      "tiles": "  ##  []$1$2..."
    }
    """
    return {
        "size": board.size,
        "tiles": serialize_board_tiles(board),
    }


def serialize_game(game: Game) -> dict[str, Any]:
    """
    Serialize a game to match client expectations.
    
    Client expects:
    {
      "id": "game-123",
      "turn": 0,
      "maxTurns": 300,
      "heroes": [...],
      "board": {...},
      "finished": false
    }
    """
    return {
        "id": game.id,
        "turn": game.turn,
        "maxTurns": game.max_turns,
        "heroes": [serialize_hero(h) for h in game.heroes],
        "board": serialize_board(game.board),
        "finished": game.finished,
    }


def serialize_game_for_hero(game: Game, hero: Hero) -> dict[str, Any]:
    """
    Serialize game with additional hero-specific information.
    
    Used for API responses that include the acting hero's context.
    """
    game_data = serialize_game(game)
    hero_data = serialize_hero(hero)
    
    return {
        "game": game_data,
        "hero": hero_data,
        "token": hero.token,
        "viewUrl": f"/{game.id}",
        "playUrl": f"/api/{game.id}/{hero.token}",
    }
