"""Game board model."""

from dataclasses import dataclass
from typing import Optional
from .tile import Tile, TileType
from .pos import Pos


@dataclass
class Board:
    """Game board with tiles."""
    tiles: list[Tile]

    @property
    def size(self) -> int:
        """Calculate board size (assumes square board)."""
        return int(len(self.tiles) ** 0.5)

    def pos_to_index(self, pos: Pos) -> Optional[int]:
        """Convert position to tile index."""
        if pos.is_in(self.size):
            return pos.x * self.size + pos.y
        return None

    def index_to_pos(self, index: int) -> Pos:
        """Convert tile index to position."""
        return Pos(index // self.size, index % self.size)

    def get(self, pos: Pos) -> Optional[Tile]:
        """Get tile at position."""
        index = self.pos_to_index(pos)
        if index is not None and 0 <= index < len(self.tiles):
            return self.tiles[index]
        return None

    def update(self, pos: Pos, tile: Tile) -> "Board":
        """Update tile at position (returns new board)."""
        index = self.pos_to_index(pos)
        if index is not None:
            new_tiles = self.tiles.copy()
            new_tiles[index] = tile
            return Board(new_tiles)
        return self

    def remove(self, pos: Pos) -> "Board":
        """Remove tile (set to Air) at position."""
        return self.update(pos, Tile.air())

    def is_air(self, pos: Pos) -> bool:
        """Check if position is air."""
        tile = self.get(pos)
        return tile is not None and tile.tile_type == TileType.AIR

    def is_wall(self, pos: Pos) -> bool:
        """Check if position is a wall."""
        tile = self.get(pos)
        return tile is not None and tile.tile_type == TileType.WALL

    def is_tavern(self, pos: Pos) -> bool:
        """Check if position is a tavern."""
        tile = self.get(pos)
        return tile is not None and tile.tile_type == TileType.TAVERN

    def is_mine(self, pos: Pos) -> bool:
        """Check if position is a mine."""
        tile = self.get(pos)
        return tile is not None and tile.tile_type == TileType.MINE

    def is_passable(self, pos: Pos) -> bool:
        """Check if position is passable (not a wall)."""
        tile = self.get(pos)
        return tile is not None and tile.tile_type != TileType.WALL

    def is_valid_position(self, pos: Pos) -> bool:
        """Check if position is valid (within bounds)."""
        return pos.is_in(self.size)

    def mirror_x(self, pos: Pos) -> Pos:
        """Mirror position across X axis."""
        return Pos(self.size - pos.x - 1, pos.y)

    def mirror_y(self, pos: Pos) -> Pos:
        """Mirror position across Y axis."""
        return Pos(pos.x, self.size - pos.y - 1)

    def mirror_xy(self, pos: Pos) -> Pos:
        """Mirror position across both axes."""
        return self.mirror_x(self.mirror_y(pos))

    def all_positions(self) -> list[tuple[Pos, Tile]]:
        """Get all positions with their tiles."""
        return [(self.index_to_pos(i), tile) for i, tile in enumerate(self.tiles)]

    def transfer_mine(self, pos: Pos, to: Optional[int]) -> "Board":
        """Transfer mine ownership at position."""
        return self.update(pos, Tile.mine(to))

    def transfer_mines(self, from_hero: int, to: Optional[int]) -> "Board":
        """Transfer all mines from one hero to another (or neutral)."""
        board = self
        for pos, tile in self.all_positions():
            if tile.tile_type == TileType.MINE and tile.owner == from_hero:
                board = board.transfer_mine(pos, to)
        return board

    def count_mines(self, owner: Optional[int] = None) -> int:
        """Count mines (optionally filtered by owner)."""
        if owner is None:
            return sum(1 for tile in self.tiles if tile.tile_type == TileType.MINE)
        else:
            return sum(
                1
                for tile in self.tiles
                if tile.tile_type == TileType.MINE and tile.owner == owner
            )

    def get_mine_positions(self, owner: Optional[int] = None) -> list[Pos]:
        """Get positions of all mines (optionally filtered by owner)."""
        positions = []
        for pos, tile in self.all_positions():
            if tile.tile_type == TileType.MINE:
                if owner is None or tile.owner == owner:
                    positions.append(pos)
        return positions

    def get_tavern_positions(self) -> list[Pos]:
        """Get positions of all taverns."""
        positions = []
        for pos, tile in self.all_positions():
            if tile.tile_type == TileType.TAVERN:
                positions.append(pos)
        return positions

    def with_tiles(self, tiles: list[Tile]) -> "Board":
        """Create new board with different tiles."""
        return Board(tiles)

    def render(self) -> str:
        """Render board as string."""
        lines = []
        for i in range(0, len(self.tiles), self.size):
            row = self.tiles[i : i + self.size]
            lines.append("".join(tile.render() for tile in row))
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()
