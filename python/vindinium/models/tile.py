"""Tile types for the game board."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TileType(str, Enum):
    """Types of tiles on the board."""
    AIR = "Air"
    WALL = "Wall"
    TAVERN = "Tavern"
    MINE = "Mine"


@dataclass(frozen=True)
class Tile:
    """A tile on the game board."""
    tile_type: TileType
    owner: Optional[int] = None

    @classmethod
    def air(cls) -> "Tile":
        """Create an air tile."""
        return cls(TileType.AIR)

    @classmethod
    def wall(cls) -> "Tile":
        """Create a wall tile."""
        return cls(TileType.WALL)

    @classmethod
    def tavern(cls) -> "Tile":
        """Create a tavern tile."""
        return cls(TileType.TAVERN)

    @classmethod
    def mine(cls, owner: Optional[int] = None) -> "Tile":
        """Create a mine tile with optional owner."""
        return cls(TileType.MINE, owner)

    def render(self) -> str:
        """Render tile as 2-character string."""
        if self.tile_type == TileType.AIR:
            return "  "
        elif self.tile_type == TileType.WALL:
            return "##"
        elif self.tile_type == TileType.TAVERN:
            return "[]"
        elif self.tile_type == TileType.MINE:
            if self.owner is None:
                return "$-"
            else:
                return f"${self.owner}"
        return "??"

    @classmethod
    def from_string(cls, s: str) -> "Tile":
        """Parse tile from 2-character string."""
        if s == "  ":
            return cls.air()
        elif s == "##":
            return cls.wall()
        elif s == "[]":
            return cls.tavern()
        elif s.startswith("$"):
            owner_char = s[1]
            if owner_char == "-":
                return cls.mine(None)
            elif owner_char.isdigit():
                return cls.mine(int(owner_char))
            else:
                return cls.mine(None)
        else:
            raise ValueError(f"Cannot parse tile: {s}")

    def is_owned_by(self, hero_id: int) -> bool:
        """Check if tile is owned by specific hero."""
        return self.tile_type == TileType.MINE and self.owner == hero_id

    def is_neutral_mine(self) -> bool:
        """Check if tile is a neutral mine."""
        return self.tile_type == TileType.MINE and self.owner is None

    def is_passable(self) -> bool:
        """Check if tile is passable (not a wall)."""
        return self.tile_type != TileType.WALL

    def __str__(self) -> str:
        return self.render()
    
    def to_dict(self) -> dict:
        """Convert tile to dictionary for serialization."""
        return {
            "tile_type": self.tile_type.value,
            "owner": self.owner,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Tile":
        """Create tile from dictionary."""
        return cls(
            tile_type=TileType(data["tile_type"]),
            owner=data["owner"],
        )
