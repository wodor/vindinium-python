"""Position and Direction models."""

from enum import Enum
from dataclasses import dataclass


class Dir(str, Enum):
    """Direction enum for hero movement."""
    STAY = "Stay"
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"
    CRASH = "Crash"

    @classmethod
    def from_string(cls, s: str) -> "Dir":
        """Parse direction from string."""
        normalized = s.lower().strip()
        mapping = {
            "north": cls.NORTH,
            "south": cls.SOUTH,
            "east": cls.EAST,
            "west": cls.WEST,
            "stay": cls.STAY,
        }
        return mapping.get(normalized, cls.STAY)


@dataclass(frozen=True)
class Pos:
    """Position on the game board."""
    x: int
    y: int

    def north(self) -> "Pos":
        """Move north (decrease x)."""
        return Pos(self.x - 1, self.y)

    def south(self) -> "Pos":
        """Move south (increase x)."""
        return Pos(self.x + 1, self.y)

    def east(self) -> "Pos":
        """Move east (increase y)."""
        return Pos(self.x, self.y + 1)

    def west(self) -> "Pos":
        """Move west (decrease y)."""
        return Pos(self.x, self.y - 1)

    def neighbors(self) -> list["Pos"]:
        """Get all 4 neighboring positions."""
        return [self.north(), self.east(), self.south(), self.west()]

    def neighbor_set(self) -> set["Pos"]:
        """Get neighbors as a set."""
        return set(self.neighbors())

    def close_to(self, other: "Pos") -> bool:
        """Check if position is adjacent to another."""
        return other in self.neighbor_set()

    def move_to(self, direction: Dir) -> "Pos":
        """Move in the given direction."""
        if direction == Dir.NORTH:
            return self.north()
        elif direction == Dir.SOUTH:
            return self.south()
        elif direction == Dir.EAST:
            return self.east()
        elif direction == Dir.WEST:
            return self.west()
        else:
            return self

    def is_in(self, size: int) -> bool:
        """Check if position is within board bounds."""
        return 0 <= self.x < size and 0 <= self.y < size

    def distance_to(self, other: "Pos") -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def is_adjacent_to(self, other: "Pos") -> bool:
        """Check if this position is adjacent to another."""
        return self.distance_to(other) == 1

    def __str__(self) -> str:
        return f"Pos({self.x}, {self.y})"
