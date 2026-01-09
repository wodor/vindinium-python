"""Map and game state generation system."""

import random
from typing import List, Optional, Tuple
from ..models.board import Board
from ..models.tile import Tile, TileType
from ..models.pos import Pos
from ..models.hero import Hero
from ..models.game import Game, Status
from .map_parser import MapParser


class Generator:
    """Generator for creating random maps and initial game states."""

    @staticmethod
    def create_random_map(size: int = 18, 
                         mine_density: float = 0.1,
                         tavern_density: float = 0.05,
                         wall_density: float = 0.3,
                         seed: Optional[int] = None) -> Board:
        """Create a random map with specified parameters.
        
        Args:
            size: Board size (must be even for symmetry)
            mine_density: Proportion of tiles that should be mines
            tavern_density: Proportion of tiles that should be taverns
            wall_density: Proportion of tiles that should be walls
            seed: Random seed for reproducible generation
            
        Returns:
            Generated Board object
        """
        if seed is not None:
            random.seed(seed)
        
        if size % 2 != 0:
            raise ValueError("Board size must be even for proper mirroring")
        
        # Create empty board
        tiles = [Tile.air() for _ in range(size * size)]
        board = Board(tiles)
        
        # Generate one quadrant and mirror it for fairness
        half_size = size // 2
        
        # Generate tiles for top-left quadrant
        for x in range(half_size):
            for y in range(half_size):
                pos = Pos(x, y)
                tile = Generator._generate_random_tile(
                    mine_density, tavern_density, wall_density
                )
                board = board.update(pos, tile)
        
        # Mirror the quadrant to create symmetric map
        board = Generator._mirror_quadrant(board, half_size)
        
        # Ensure spawn positions are clear
        board = Generator._ensure_spawn_positions(board)
        
        # Validate the generated map
        if not MapParser.validate_map(board):
            # Retry with different parameters if validation fails
            return Generator.create_random_map(
                size, mine_density * 0.8, tavern_density * 0.8, wall_density * 0.8, seed
            )
        
        return board

    @staticmethod
    def _generate_random_tile(mine_density: float, 
                            tavern_density: float, 
                            wall_density: float) -> Tile:
        """Generate a random tile based on density parameters."""
        rand = random.random()
        
        if rand < wall_density:
            return Tile.wall()
        elif rand < wall_density + mine_density:
            return Tile.mine(None)  # Neutral mine
        elif rand < wall_density + mine_density + tavern_density:
            return Tile.tavern()
        else:
            return Tile.air()

    @staticmethod
    def _mirror_quadrant(board: Board, half_size: int) -> Board:
        """Mirror top-left quadrant to create symmetric map."""
        size = board.size
        
        for x in range(half_size):
            for y in range(half_size):
                source_pos = Pos(x, y)
                source_tile = board.get(source_pos)
                
                if source_tile is None:
                    continue
                
                # Mirror to other quadrants
                positions = [
                    Pos(x, size - 1 - y),              # Top-right
                    Pos(size - 1 - x, y),              # Bottom-left
                    Pos(size - 1 - x, size - 1 - y)    # Bottom-right
                ]
                
                for pos in positions:
                    board = board.update(pos, source_tile)
        
        return board

    @staticmethod
    def _ensure_spawn_positions(board: Board) -> Board:
        """Ensure spawn positions are clear (air tiles)."""
        size = board.size
        
        # Define spawn positions (corners with some offset)
        spawn_offset = 2
        spawn_positions = [
            Pos(spawn_offset, spawn_offset),                           # Top-left
            Pos(spawn_offset, size - 1 - spawn_offset),               # Top-right
            Pos(size - 1 - spawn_offset, size - 1 - spawn_offset),    # Bottom-right
            Pos(size - 1 - spawn_offset, spawn_offset)                # Bottom-left
        ]
        
        # Clear spawn positions and surrounding area
        for spawn_pos in spawn_positions:
            # Clear the spawn position itself
            board = board.update(spawn_pos, Tile.air())
            
            # Clear adjacent positions for movement
            for neighbor in spawn_pos.neighbors():
                if board.is_valid_position(neighbor):
                    board = board.update(neighbor, Tile.air())
        
        return board

    @staticmethod
    def create_initial_game_state(board: Board, 
                                game_id: str = "test-game",
                                max_turns: int = 300,
                                training: bool = True) -> Game:
        """Create initial game state with heroes at spawn positions.
        
        Args:
            board: Game board
            game_id: Unique game identifier
            max_turns: Maximum number of turns
            training: Whether this is a training game
            
        Returns:
            Initial Game object
        """
        # Find spawn positions
        spawn_positions = MapParser.find_spawn_positions(board)
        
        # Create heroes at spawn positions
        heroes = []
        for i in range(4):
            hero = Hero.create(
                id=i + 1,
                name=f"Hero{i + 1}",
                user_id=None,
                elo=None,
                pos=spawn_positions[i],
                token=f"token-{i + 1}"
            )
            heroes.append(hero)
        
        # Create initial game state
        game = Game(
            id=game_id,
            training=training,
            board=board,
            hero1=heroes[0],
            hero2=heroes[1],
            hero3=heroes[2],
            hero4=heroes[3],
            spawn_pos=spawn_positions[0],  # Base spawn position
            turn=0,
            max_turns=max_turns,
            status=Status.CREATED
        )
        
        return game

    @staticmethod
    def get_default_map_small() -> str:
        """Get a small default map for testing."""
        return """########################
##[]        []        ##
##    ####    ####    ##
##$-  ####    ##[]    ##
##    ####    ####    ##
##        $-          ##
##    ##########      ##
##    ##########      ##
########    $-        ##
########      ####    ##
##[]  ##      ####  $-##
########################"""

    @staticmethod
    def get_default_map_medium() -> str:
        """Get a medium-sized default map for testing."""
        return """##############################
##[]            []          ##
##    ########    ########  ##
##$-  ########    ##[]  ##  ##
##    ########    ########  ##
##            $-            ##
##    ################      ##
##    ################      ##
##        ################  ##
##        ################  ##
############    $-          ##
############      ######    ##
##[]  ##      ######    $-  ##
############      ######    ##
##############################"""

    @staticmethod
    def get_default_map_large() -> str:
        """Get a large default map for testing."""
        return """####################################
##[]                []            ##
##    ############    ##########  ##
##$-  ############    ##[]    ##  ##
##    ############    ##########  ##
##                $-              ##
##    ##################          ##
##    ##################          ##
##        ##################      ##
##        ##################      ##
##        ##################      ##
##        ##################      ##
############    $-                ##
############      ##########      ##
##[]  ##      ##########    $-    ##
############      ##########      ##
##        []              []      ##
####################################"""

    @staticmethod
    def create_test_board(map_string: str) -> Board:
        """Create a board from a test map string.
        
        Args:
            map_string: String representation of the map
            
        Returns:
            Parsed Board object
        """
        return MapParser.parse_map(map_string)

    @staticmethod
    def create_minimal_test_game(size: int = 6) -> Game:
        """Create a minimal game for testing purposes.
        
        Args:
            size: Board size
            
        Returns:
            Test Game object
        """
        # Create simple test map
        map_str = Generator._create_minimal_map_string(size)
        board = MapParser.parse_map(map_str)
        
        return Generator.create_initial_game_state(board, "test-minimal")

    @staticmethod
    def _create_minimal_map_string(size: int) -> str:
        """Create a minimal map string for testing."""
        if size < 4:
            raise ValueError("Size must be at least 4 for hero spawns")
        
        lines = []
        for x in range(size):
            line = ""
            for y in range(size):
                if x == 0 or x == size - 1 or y == 0 or y == size - 1:
                    line += "##"  # Walls around border
                elif (x == 1 and y == 1) or (x == 1 and y == size - 2) or \
                     (x == size - 2 and y == 1) or (x == size - 2 and y == size - 2):
                    line += "  "  # Spawn positions
                elif x == size // 2 and y == size // 2:
                    line += "$-"  # Central mine
                elif (x + y) % 3 == 0:
                    line += "[]"  # Some taverns
                else:
                    line += "  "  # Air
            lines.append(line)
        
        return "\n".join(lines)

    @staticmethod
    def create_symmetric_map(size: int, pattern: str = "cross") -> Board:
        """Create a symmetric map with a specific pattern.
        
        Args:
            size: Board size (must be even)
            pattern: Pattern type ("cross", "corners", "center")
            
        Returns:
            Generated symmetric Board
        """
        if size % 2 != 0:
            raise ValueError("Size must be even for symmetry")
        
        tiles = [Tile.air() for _ in range(size * size)]
        board = Board(tiles)
        
        # Add border walls
        for i in range(size):
            board = board.update(Pos(0, i), Tile.wall())
            board = board.update(Pos(size - 1, i), Tile.wall())
            board = board.update(Pos(i, 0), Tile.wall())
            board = board.update(Pos(i, size - 1), Tile.wall())
        
        if pattern == "cross":
            board = Generator._add_cross_pattern(board, size)
        elif pattern == "corners":
            board = Generator._add_corner_pattern(board, size)
        elif pattern == "center":
            board = Generator._add_center_pattern(board, size)
        
        # Ensure spawn positions
        board = Generator._ensure_spawn_positions(board)
        
        return board

    @staticmethod
    def _add_cross_pattern(board: Board, size: int) -> Board:
        """Add cross pattern to board."""
        center = size // 2
        
        # Vertical line
        for x in range(2, size - 2):
            if x != center - 1 and x != center:
                board = board.update(Pos(x, center), Tile.wall())
        
        # Horizontal line
        for y in range(2, size - 2):
            if y != center - 1 and y != center:
                board = board.update(Pos(center, y), Tile.wall())
        
        # Add some mines and taverns
        board = board.update(Pos(center - 1, center - 1), Tile.mine(None))
        board = board.update(Pos(center, center), Tile.mine(None))
        board = board.update(Pos(center - 2, center - 2), Tile.tavern())
        board = board.update(Pos(center + 1, center + 1), Tile.tavern())
        
        return board

    @staticmethod
    def _add_corner_pattern(board: Board, size: int) -> Board:
        """Add corner pattern to board."""
        # Add mines in corners (inside walls)
        board = board.update(Pos(2, 2), Tile.mine(None))
        board = board.update(Pos(2, size - 3), Tile.mine(None))
        board = board.update(Pos(size - 3, 2), Tile.mine(None))
        board = board.update(Pos(size - 3, size - 3), Tile.mine(None))
        
        # Add taverns near center
        center = size // 2
        board = board.update(Pos(center - 1, center - 1), Tile.tavern())
        board = board.update(Pos(center, center), Tile.tavern())
        
        return board

    @staticmethod
    def _add_center_pattern(board: Board, size: int) -> Board:
        """Add center pattern to board."""
        center = size // 2
        
        # Central mine cluster
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    board = board.update(Pos(center + dx, center + dy), Tile.mine(None))
                elif abs(dx) + abs(dy) == 1:
                    board = board.update(Pos(center + dx, center + dy), Tile.tavern())
        
        return board