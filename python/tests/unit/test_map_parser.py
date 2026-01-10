"""Property-based tests for MapParser round-trip invariants."""

import pytest
from hypothesis import given, strategies as st, assume
from vindinium.models.board import Board
from vindinium.models.tile import Tile, TileType
from vindinium.system.map_parser import MapParser


# Hypothesis strategies for generating tiles
@st.composite
def tile_strategy(draw):
    """Generate a valid tile."""
    tile_type = draw(st.sampled_from([TileType.AIR, TileType.WALL, TileType.TAVERN, TileType.MINE]))
    
    if tile_type == TileType.MINE:
        # Mine can be neutral or owned by hero 1-4
        owner = draw(st.sampled_from([None, 1, 2, 3, 4]))
        return Tile.mine(owner)
    elif tile_type == TileType.AIR:
        return Tile.air()
    elif tile_type == TileType.WALL:
        return Tile.wall()
    elif tile_type == TileType.TAVERN:
        return Tile.tavern()


@st.composite
def valid_board_strategy(draw):
    """Generate a valid Board with even size and sufficient air tiles.
    
    The board must:
    - Have even dimensions (N*N where N is even)
    - Contain at least 4 air tiles for spawn positions
    - Have walls on all edges (to prevent parsing issues with trailing spaces)
    - Be parseable and renderable
    """
    # Size must be even (requirement from spec)
    size = draw(st.integers(min_value=4, max_value=12).filter(lambda x: x % 2 == 0))
    
    total_tiles = size * size
    
    # Create tiles list initialized with None
    tiles = [None] * total_tiles
    
    # Add walls around the perimeter (this ensures rendered strings don't end with spaces)
    for i in range(size):
        # Top row
        tiles[i] = Tile.wall()
        # Bottom row
        tiles[(size - 1) * size + i] = Tile.wall()
        # Left column
        tiles[i * size] = Tile.wall()
        # Right column
        tiles[i * size + (size - 1)] = Tile.wall()
    
    # Count how many tiles are left to fill
    filled_count = 0
    for tile in tiles:
        if tile is not None:
            filled_count += 1
    
    remaining_count = total_tiles - filled_count
    
    # Ensure we have at least 4 air tiles for spawn positions
    min_air_tiles = max(4, remaining_count // 4)
    air_tiles_count = draw(st.integers(min_value=min_air_tiles, max_value=remaining_count))
    
    # Fill remaining interior tiles
    interior_tiles = []
    for _ in range(air_tiles_count):
        interior_tiles.append(Tile.air())
    
    for _ in range(remaining_count - air_tiles_count):
        interior_tiles.append(draw(tile_strategy()))
    
    # Shuffle interior tiles
    draw(st.randoms()).shuffle(interior_tiles)
    
    # Place interior tiles
    interior_idx = 0
    for i in range(total_tiles):
        if tiles[i] is None:
            tiles[i] = interior_tiles[interior_idx]
            interior_idx += 1
    
    board = Board(tiles)
    
    # Validate the board meets minimum requirements
    assume(MapParser.validate_map(board))
    
    return board


class TestMapParserRoundTrip:
    """Property-based tests for map parsing round-trip integrity."""
    
    @given(valid_board_strategy())
    def test_parse_render_round_trip(self, board: Board):
        """Test that parsing then rendering produces equivalent Board.
        
        Property: MapParser.parse_map(MapParser.render_board(board)) == board
        
        This verifies that:
        1. Any valid board can be rendered to a string
        2. The rendered string can be parsed back
        3. The parsed board is equivalent to the original
        """
        # Render the board to a string
        rendered_string = MapParser.render_board(board)
        
        # Parse the rendered string back to a board
        parsed_board = MapParser.parse_map(rendered_string)
        
        # Verify the boards are equivalent
        assert len(board.tiles) == len(parsed_board.tiles), \
            "Boards should have same number of tiles"
        
        assert board.size == parsed_board.size, \
            "Boards should have same size"
        
        # Check each tile matches
        for i, (original_tile, parsed_tile) in enumerate(zip(board.tiles, parsed_board.tiles)):
            assert original_tile.tile_type == parsed_tile.tile_type, \
                f"Tile {i} type mismatch: {original_tile.tile_type} != {parsed_tile.tile_type}"
            assert original_tile.owner == parsed_tile.owner, \
                f"Tile {i} owner mismatch: {original_tile.owner} != {parsed_tile.owner}"
    
    @given(valid_board_strategy())
    def test_rendered_string_length_invariant(self, board: Board):
        """Test that rendered string has correct length.
        
        Property: len(render_board(board)) == (size * 2) * size + (size - 1)
        
        The rendered string should have:
        - Each tile is 2 characters
        - Each row has size tiles, so size * 2 characters per row
        - There are size rows
        - There are (size - 1) newline characters separating rows
        """
        rendered_string = MapParser.render_board(board)
        
        # Calculate expected length
        size = board.size
        # Each row: size tiles * 2 chars per tile = size * 2 chars
        # Total rows: size
        # Newlines between rows: size - 1
        expected_length = (size * 2) * size + (size - 1)
        
        actual_length = len(rendered_string)
        
        assert actual_length == expected_length, \
            f"Rendered string length mismatch: expected {expected_length}, got {actual_length}"
    
    @given(valid_board_strategy())
    def test_render_has_valid_tile_strings(self, board: Board):
        """Test that rendered string contains only valid tile representations.
        
        Property: All 2-character sequences in rendered string are valid tiles
        
        Valid tiles: '  ', '##', '[]', '$-', '$1', '$2', '$3', '$4'
        """
        rendered_string = MapParser.render_board(board)
        
        # Split by newlines to get rows
        rows = rendered_string.split('\n')
        
        assert len(rows) == board.size, \
            f"Should have {board.size} rows, got {len(rows)}"
        
        valid_tile_strings = {'  ', '##', '[]', '$-', '$1', '$2', '$3', '$4'}
        
        for row_idx, row in enumerate(rows):
            # Each row should have exactly size * 2 characters
            assert len(row) == board.size * 2, \
                f"Row {row_idx} should have {board.size * 2} chars, got {len(row)}"
            
            # Check each 2-char tile string
            for i in range(0, len(row), 2):
                tile_str = row[i:i+2]
                assert tile_str in valid_tile_strings, \
                    f"Invalid tile string '{tile_str}' at row {row_idx}, position {i//2}"
    
    @given(valid_board_strategy())
    def test_round_trip_preserves_mine_ownership(self, board: Board):
        """Test that round-trip preserves mine ownership information.
        
        Property: Mine ownership is preserved through render/parse cycle
        """
        # Count mines by owner in original board
        original_mine_counts = {}
        for tile in board.tiles:
            if tile.tile_type == TileType.MINE:
                owner = tile.owner
                original_mine_counts[owner] = original_mine_counts.get(owner, 0) + 1
        
        # Perform round-trip
        rendered = MapParser.render_board(board)
        parsed = MapParser.parse_map(rendered)
        
        # Count mines by owner in parsed board
        parsed_mine_counts = {}
        for tile in parsed.tiles:
            if tile.tile_type == TileType.MINE:
                owner = tile.owner
                parsed_mine_counts[owner] = parsed_mine_counts.get(owner, 0) + 1
        
        assert original_mine_counts == parsed_mine_counts, \
            f"Mine ownership counts don't match: {original_mine_counts} != {parsed_mine_counts}"
    
    @given(valid_board_strategy())
    def test_round_trip_preserves_all_tile_types(self, board: Board):
        """Test that round-trip preserves counts of all tile types.
        
        Property: Tile type distribution is preserved through render/parse cycle
        """
        # Count tiles by type in original board
        original_counts = MapParser.count_tile_types(board)
        
        # Perform round-trip
        rendered = MapParser.render_board(board)
        parsed = MapParser.parse_map(rendered)
        
        # Count tiles by type in parsed board
        parsed_counts = MapParser.count_tile_types(parsed)
        
        assert original_counts == parsed_counts, \
            f"Tile type counts don't match: {original_counts} != {parsed_counts}"
    
    @given(valid_board_strategy())
    def test_parsed_board_is_valid(self, board: Board):
        """Test that parsed board passes validation.
        
        Property: If original board is valid, parsed board must be valid
        """
        # Original board should be valid (ensured by strategy)
        assert MapParser.validate_map(board)
        
        # Perform round-trip
        rendered = MapParser.render_board(board)
        parsed = MapParser.parse_map(rendered)
        
        # Parsed board should also be valid
        assert MapParser.validate_map(parsed), \
            "Parsed board should be valid if original was valid"


class TestMapParserEdgeCases:
    """Test edge cases for map parsing."""
    
    def test_minimum_size_board(self):
        """Test round-trip with minimum valid board size (4x4)."""
        # Create a minimal 4x4 board
        tiles = [
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
        ]
        board = Board(tiles)
        
        # Round-trip test
        rendered = MapParser.render_board(board)
        parsed = MapParser.parse_map(rendered)
        
        assert board.size == parsed.size
        assert len(board.tiles) == len(parsed.tiles)
    
    def test_all_mine_types(self):
        """Test round-trip with all mine ownership types."""
        # Create a board with mines owned by different heroes, surrounded by walls
        # Must have at least 4 air tiles for validation
        tiles = [
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.mine(None), Tile.mine(1), Tile.wall(),
            Tile.wall(), Tile.mine(2), Tile.mine(3), Tile.wall(),
            Tile.wall(), Tile.mine(4), Tile.wall(), Tile.wall(),
        ]
        # This is a 4x6 board, we need square - let's make it 6x6
        tiles = [
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.mine(None), Tile.mine(1), Tile.mine(2), Tile.mine(3), Tile.wall(),
            Tile.wall(), Tile.mine(4), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
        ]
        board = Board(tiles)
        
        # Round-trip test
        rendered = MapParser.render_board(board)
        parsed = MapParser.parse_map(rendered)
        
        # Verify all mine types preserved
        for i, (orig, parsed_tile) in enumerate(zip(tiles, parsed.tiles)):
            if orig.tile_type == TileType.MINE:
                assert parsed_tile.tile_type == TileType.MINE
                assert parsed_tile.owner == orig.owner, \
                    f"Mine {i} owner mismatch: {orig.owner} != {parsed_tile.owner}"
    
    def test_all_tile_types_represented(self):
        """Test round-trip with all tile types."""
        # Create a board with all tile types, surrounded by walls
        # Must have at least 4 air tiles for validation
        tiles = [
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.tavern(), Tile.mine(None), Tile.mine(1), Tile.mine(2), Tile.wall(),
            Tile.wall(), Tile.air(), Tile.air(), Tile.air(), Tile.air(), Tile.wall(),
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
            Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(), Tile.wall(),
        ]
        board = Board(tiles)
        
        # Round-trip test
        rendered = MapParser.render_board(board)
        parsed = MapParser.parse_map(rendered)
        
        # Verify all tile types are preserved
        for i, (orig, parsed_tile) in enumerate(zip(tiles, parsed.tiles)):
            assert orig.tile_type == parsed_tile.tile_type
            assert orig.owner == parsed_tile.owner
