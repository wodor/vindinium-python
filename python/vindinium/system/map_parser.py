"""Map parsing and validation system."""

import re
from typing import Optional, List, Tuple
from ..models.board import Board
from ..models.tile import Tile, TileType
from ..models.pos import Pos


class MapParser:
    """Parser for converting string maps to Board objects."""

    @staticmethod
    def parse_map(map_string: str) -> Board:
        """Parse string representation into Board object.
        
        Args:
            map_string: Multi-line string representing the board
            
        Returns:
            Board object with parsed tiles
            
        Raises:
            ValueError: If map format is invalid
        """
        # Clean up the map string
        lines = map_string.strip().split('\n')
        lines = [line.rstrip() for line in lines if line.strip()]
        
        if not lines:
            raise ValueError("Empty map string")
        
        # Validate square dimensions
        size = len(lines)
        for i, line in enumerate(lines):
            # Each line should have size * 2 characters (2 chars per tile)
            if len(line) != size * 2:
                raise ValueError(f"Line {i} has length {len(line)}, expected {size * 2}")
        
        # Parse tiles
        tiles = []
        for line in lines:
            for i in range(0, len(line), 2):
                tile_str = line[i:i+2]
                try:
                    tile = Tile.from_string(tile_str)
                    tiles.append(tile)
                except ValueError as e:
                    raise ValueError(f"Invalid tile '{tile_str}': {e}")
        
        board = Board(tiles)
        
        # Validate the parsed board
        if not MapParser.validate_map(board):
            raise ValueError("Map validation failed")
        
        return board

    @staticmethod
    def validate_map(board: Board) -> bool:
        """Validate map has required elements and proper dimensions.
        
        Args:
            board: Board to validate
            
        Returns:
            True if valid, False otherwise
        """
        size = board.size
        
        # Check if board is square
        if len(board.tiles) != size * size:
            return False
        
        # Check for spawn positions (at least 4 air tiles for heroes)
        air_positions = []
        for pos, tile in board.all_positions():
            if tile.tile_type == TileType.AIR:
                air_positions.append(pos)
        
        if len(air_positions) < 4:
            return False
        
        # Validate that we have at least some passable tiles
        passable_count = sum(1 for tile in board.tiles if tile.is_passable())
        if passable_count < 4:  # Need at least 4 for heroes
            return False
        
        return True

    @staticmethod
    def find_spawn_positions(board: Board) -> List[Pos]:
        """Find suitable spawn positions for heroes.
        
        Args:
            board: Board to analyze
            
        Returns:
            List of 4 spawn positions (mirrored for fairness)
        """
        size = board.size
        
        # Find air tiles that could serve as spawn positions
        air_positions = []
        for pos, tile in board.all_positions():
            if tile.tile_type == TileType.AIR:
                air_positions.append(pos)
        
        if len(air_positions) < 4:
            raise ValueError("Not enough air tiles for spawn positions")
        
        # Try to find a good spawn position (preferably not in center)
        # Look for positions near corners or edges
        spawn_candidates = []
        for pos in air_positions:
            # Prefer positions closer to edges
            edge_distance = min(pos.x, pos.y, size - 1 - pos.x, size - 1 - pos.y)
            spawn_candidates.append((edge_distance, pos))
        
        # Sort by edge distance (closer to edge is better)
        spawn_candidates.sort(key=lambda x: x[0])
        
        # Take the first suitable position
        base_pos = spawn_candidates[0][1]
        
        # Generate mirrored positions
        spawn_positions = [
            base_pos,                           # Hero 1: Original
            board.mirror_x(base_pos),          # Hero 2: X-mirror
            board.mirror_xy(base_pos),         # Hero 3: XY-mirror (diagonal)
            board.mirror_y(base_pos)           # Hero 4: Y-mirror
        ]
        
        # Validate all spawn positions are air tiles
        for i, pos in enumerate(spawn_positions):
            if not board.is_air(pos):
                # If mirrored position is not air, find nearest air tile
                spawn_positions[i] = MapParser._find_nearest_air(board, pos)
        
        return spawn_positions

    @staticmethod
    def _find_nearest_air(board: Board, target: Pos) -> Pos:
        """Find nearest air tile to target position.
        
        Args:
            board: Board to search
            target: Target position
            
        Returns:
            Nearest air position
        """
        # BFS to find nearest air tile
        from collections import deque
        
        queue = deque([target])
        visited = {target}
        
        while queue:
            pos = queue.popleft()
            
            if board.is_air(pos):
                return pos
            
            for neighbor in pos.neighbors():
                if neighbor not in visited and board.is_valid_position(neighbor):
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Fallback: return first air tile found
        for pos, tile in board.all_positions():
            if tile.tile_type == TileType.AIR:
                return pos
        
        raise ValueError("No air tiles found on board")

    @staticmethod
    def render_board(board: Board) -> str:
        """Render board back to string format.
        
        Args:
            board: Board to render
            
        Returns:
            String representation of the board
        """
        return board.render()

    @staticmethod
    def parse_tile_string(tile_str: str) -> Tile:
        """Parse a single tile from 2-character string.
        
        Args:
            tile_str: 2-character tile representation
            
        Returns:
            Parsed Tile object
        """
        return Tile.from_string(tile_str)

    @staticmethod
    def validate_tile_types(board: Board) -> bool:
        """Validate that board contains only valid tile types.
        
        Args:
            board: Board to validate
            
        Returns:
            True if all tiles are valid
        """
        valid_types = {TileType.AIR, TileType.WALL, TileType.TAVERN, TileType.MINE}
        
        for tile in board.tiles:
            if tile.tile_type not in valid_types:
                return False
            
            # Validate mine ownership
            if tile.tile_type == TileType.MINE:
                if tile.owner is not None and not (1 <= tile.owner <= 4):
                    return False
        
        return True

    @staticmethod
    def count_tile_types(board: Board) -> dict[TileType, int]:
        """Count tiles by type.
        
        Args:
            board: Board to analyze
            
        Returns:
            Dictionary mapping tile types to counts
        """
        counts = {tile_type: 0 for tile_type in TileType}
        
        for tile in board.tiles:
            counts[tile.tile_type] += 1
        
        return counts