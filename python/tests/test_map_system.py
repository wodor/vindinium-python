"""Tests for map parsing and generation system."""

import pytest
from vindinium.system.map_parser import MapParser
from vindinium.system.generator import Generator
from vindinium.models.board import Board
from vindinium.models.tile import Tile, TileType
from vindinium.models.pos import Pos


class TestMapParser:
    """Test MapParser functionality."""

    def test_parse_simple_map(self):
        """Test parsing a simple map."""
        map_str = """##########
##      ##
##  []  ##
##      ##
##########"""
        
        board = MapParser.parse_map(map_str)
        assert board.size == 5
        assert len(board.tiles) == 25
        
        # Check specific tiles
        assert board.get(Pos(0, 0)).tile_type == TileType.WALL
        assert board.get(Pos(1, 1)).tile_type == TileType.AIR
        assert board.get(Pos(2, 2)).tile_type == TileType.TAVERN

    def test_parse_map_with_mines(self):
        """Test parsing map with different mine types."""
        map_str = """############
##$-$1    ##
##$2$3    ##
##  []    ##
##        ##
############"""
        
        board = MapParser.parse_map(map_str)
        
        # Check mine types
        neutral_mine = board.get(Pos(1, 1))
        assert neutral_mine.tile_type == TileType.MINE
        assert neutral_mine.owner is None
        
        owned_mine1 = board.get(Pos(1, 2))
        assert owned_mine1.tile_type == TileType.MINE
        assert owned_mine1.owner == 1
        
        owned_mine2 = board.get(Pos(2, 1))
        assert owned_mine2.tile_type == TileType.MINE
        assert owned_mine2.owner == 2

    def test_parse_invalid_map_non_square(self):
        """Test that non-square maps raise ValueError."""
        map_str = """########
##    ##
########"""  # 4x3, not square
        
        with pytest.raises(ValueError, match="expected"):
            MapParser.parse_map(map_str)

    def test_parse_invalid_tile(self):
        """Test that invalid tiles raise ValueError."""
        map_str = """########
##XX  ##
########
########"""  # XX is invalid
        
        with pytest.raises(ValueError, match="Invalid tile"):
            MapParser.parse_map(map_str)

    def test_validate_map_success(self):
        """Test successful map validation."""
        map_str = """############
##        ##
##  []    ##
##$-      ##
##        ##
############"""
        
        board = MapParser.parse_map(map_str)
        assert MapParser.validate_map(board)

    def test_validate_map_insufficient_air(self):
        """Test map validation fails with insufficient air tiles."""
        # Create board with only walls and one air tile
        tiles = [Tile.wall() for _ in range(16)]
        tiles[5] = Tile.air()  # Only one air tile
        board = Board(tiles)
        
        assert not MapParser.validate_map(board)

    def test_find_spawn_positions(self):
        """Test finding spawn positions."""
        map_str = """################
##            ##
##  []        ##
##            ##
##  $-        ##
##            ##
##            ##
################"""
        
        board = MapParser.parse_map(map_str)
        spawn_positions = MapParser.find_spawn_positions(board)
        
        assert len(spawn_positions) == 4
        # All spawn positions should be air tiles
        for pos in spawn_positions:
            assert board.is_air(pos)

    def test_render_board_round_trip(self):
        """Test that parsing then rendering produces equivalent result."""
        map_str = """############
##$-[]    ##
##        ##
##  $1    ##
##        ##
############"""
        
        board = MapParser.parse_map(map_str)
        rendered = MapParser.render_board(board)
        
        # Parse the rendered string back
        board2 = MapParser.parse_map(rendered)
        
        # Should have same tiles
        assert len(board.tiles) == len(board2.tiles)
        for i, (tile1, tile2) in enumerate(zip(board.tiles, board2.tiles)):
            assert tile1.tile_type == tile2.tile_type
            assert tile1.owner == tile2.owner

    def test_count_tile_types(self):
        """Test counting tile types."""
        map_str = """############
##$-[]    ##
##        ##
##  $1    ##
##        ##
############"""
        
        board = MapParser.parse_map(map_str)
        counts = MapParser.count_tile_types(board)
        
        assert counts[TileType.WALL] == 20  # Border walls
        assert counts[TileType.AIR] == 13   # Empty spaces
        assert counts[TileType.MINE] == 2   # $- and $1
        assert counts[TileType.TAVERN] == 1 # []


class TestGenerator:
    """Test Generator functionality."""

    def test_create_random_map(self):
        """Test creating a random map."""
        board = Generator.create_random_map(size=8, seed=42)
        
        assert board.size == 8
        assert len(board.tiles) == 64
        assert MapParser.validate_map(board)

    def test_create_random_map_invalid_size(self):
        """Test that odd sizes raise ValueError."""
        with pytest.raises(ValueError, match="even"):
            Generator.create_random_map(size=7)

    def test_create_initial_game_state(self):
        """Test creating initial game state."""
        map_str = Generator.get_default_map_small()
        board = MapParser.parse_map(map_str)
        
        game = Generator.create_initial_game_state(board, "test-123")
        
        assert game.id == "test-123"
        assert game.turn == 0
        assert game.max_turns == 300
        assert len(game.heroes) == 4
        
        # All heroes should be at different positions
        positions = [hero.pos for hero in game.heroes]
        assert len(set(positions)) == 4
        
        # All heroes should start with full health and no gold
        for hero in game.heroes:
            assert hero.life == 100
            assert hero.gold == 0

    def test_default_maps_parse_correctly(self):
        """Test that all default maps parse correctly."""
        maps = [
            Generator.get_default_map_small(),
            Generator.get_default_map_medium(),
            Generator.get_default_map_large()
        ]
        
        for map_str in maps:
            board = MapParser.parse_map(map_str)
            assert MapParser.validate_map(board)
            
            # Should be able to find spawn positions
            spawn_positions = MapParser.find_spawn_positions(board)
            assert len(spawn_positions) == 4

    def test_create_test_board(self):
        """Test creating test board from string."""
        map_str = Generator.get_default_map_small()
        board = Generator.create_test_board(map_str)
        
        assert isinstance(board, Board)
        assert MapParser.validate_map(board)

    def test_create_minimal_test_game(self):
        """Test creating minimal test game."""
        game = Generator.create_minimal_test_game(size=6)
        
        assert game.id == "test-minimal"
        assert game.board.size == 6
        assert len(game.heroes) == 4
        assert MapParser.validate_map(game.board)

    def test_create_symmetric_map_cross(self):
        """Test creating symmetric map with cross pattern."""
        board = Generator.create_symmetric_map(size=8, pattern="cross")
        
        assert board.size == 8
        assert MapParser.validate_map(board)

    def test_create_symmetric_map_corners(self):
        """Test creating symmetric map with corner pattern."""
        board = Generator.create_symmetric_map(size=8, pattern="corners")
        
        assert board.size == 8
        assert MapParser.validate_map(board)

    def test_create_symmetric_map_center(self):
        """Test creating symmetric map with center pattern."""
        board = Generator.create_symmetric_map(size=8, pattern="center")
        
        assert board.size == 8
        assert MapParser.validate_map(board)

    def test_symmetric_map_invalid_size(self):
        """Test that odd sizes raise ValueError for symmetric maps."""
        with pytest.raises(ValueError, match="even"):
            Generator.create_symmetric_map(size=7)


class TestMapParsingEdgeCases:
    """Test edge cases in map parsing."""

    def test_empty_map_string(self):
        """Test that empty map string raises ValueError."""
        with pytest.raises(ValueError, match="Empty map"):
            MapParser.parse_map("")

    def test_map_with_whitespace_lines(self):
        """Test handling maps with whitespace-only lines."""
        map_str = """########
##    ##

##    ##
########"""  # Empty line in middle
        
        board = MapParser.parse_map(map_str)
        assert board.size == 4

    def test_find_nearest_air_tile(self):
        """Test finding nearest air tile when spawn position is blocked."""
        # Create map where mirrored positions might be walls
        map_str = """################
##            ##
##  ########  ##
##  ##    ##  ##
##  ##    ##  ##
##  ########  ##
##            ##
################"""
        
        board = MapParser.parse_map(map_str)
        spawn_positions = MapParser.find_spawn_positions(board)
        
        # Should find valid air positions for all heroes
        assert len(spawn_positions) == 4
        for pos in spawn_positions:
            assert board.is_air(pos)

    def test_parse_tile_string_directly(self):
        """Test parsing individual tile strings."""
        assert MapParser.parse_tile_string("  ").tile_type == TileType.AIR
        assert MapParser.parse_tile_string("##").tile_type == TileType.WALL
        assert MapParser.parse_tile_string("[]").tile_type == TileType.TAVERN
        assert MapParser.parse_tile_string("$-").tile_type == TileType.MINE
        assert MapParser.parse_tile_string("$-").owner is None
        assert MapParser.parse_tile_string("$1").owner == 1

    def test_validate_tile_types(self):
        """Test tile type validation."""
        map_str = """##########
##$1    ##
##[]    ##
##      ##
##########"""
        
        board = MapParser.parse_map(map_str)
        assert MapParser.validate_tile_types(board)
        
        # Test with invalid mine owner
        invalid_tiles = [Tile.air(), Tile.mine(5)]  # Owner 5 is invalid
        invalid_board = Board(invalid_tiles)
        assert not MapParser.validate_tile_types(invalid_board)