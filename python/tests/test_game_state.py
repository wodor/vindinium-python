"""Property-based tests for Game initialization invariants."""

from hypothesis import given, strategies as st, settings
from vindinium.models import Pos, Hero, Board, Game, Status
from vindinium.system.generator import Generator
from vindinium.system.map_parser import MapParser


class TestGameInitializationProperties:
    """Property-based tests for Game initialization."""

    @given(
        size=st.integers(min_value=6, max_value=20).filter(lambda x: x % 2 == 0)
    )
    @settings(max_examples=50)
    def test_property_1_game_initialization_invariants(self, size):
        """
        Property 1: Game Initialization Invariants
        For any valid board size, when a game is initialized via Generator.create_initial_game_state,
        the following invariants must hold:
        1. Exactly 4 heroes exist
        2. All heroes have 100 Life (MAX_LIFE)
        3. All heroes have 0 Gold
        4. All spawn positions are unique
        5. Spawn positions are mirrored (symmetrically placed)
        6. Hero 1 is the current hero at turn 0
        
        **Feature: vindinium-python-rewrite, Property 1: Game Initialization Invariants**
        **Validates: Requirements 4.1, 1.4**
        """
        # Create a random map with the given size
        board = Generator.create_random_map(size=size, seed=42)
        
        # Create initial game state
        game = Generator.create_initial_game_state(board, game_id=f"test-{size}")
        
        # Invariant 1: Exactly 4 heroes must exist
        assert len(game.heroes) == 4, "Game must have exactly 4 heroes"
        
        # Invariant 2: All heroes have 100 Life
        for i, hero in enumerate(game.heroes, start=1):
            assert hero.life == Hero.MAX_LIFE, f"Hero {i} must start with {Hero.MAX_LIFE} life"
        
        # Invariant 3: All heroes have 0 Gold
        for i, hero in enumerate(game.heroes, start=1):
            assert hero.gold == 0, f"Hero {i} must start with 0 gold"
        
        # Invariant 4: All spawn positions are unique
        positions = [hero.pos for hero in game.heroes]
        assert len(set(positions)) == 4, "All hero spawn positions must be unique"
        
        # Invariant 5: Spawn positions are mirrored (symmetrically placed)
        # Based on Game.spawn_pos_of method, heroes should be at mirrored positions
        hero2_pos = game.hero2.pos
        hero3_pos = game.hero3.pos
        hero4_pos = game.hero4.pos
        
        # Hero 2 should be mirror_x of Hero 1
        expected_hero2_pos = game.board.mirror_x(game.spawn_pos)
        assert hero2_pos == expected_hero2_pos, f"Hero 2 position {hero2_pos} must be X-mirror of spawn {game.spawn_pos}"
        
        # Hero 3 should be mirror_xy of Hero 1
        expected_hero3_pos = game.board.mirror_xy(game.spawn_pos)
        assert hero3_pos == expected_hero3_pos, f"Hero 3 position {hero3_pos} must be XY-mirror of spawn {game.spawn_pos}"
        
        # Hero 4 should be mirror_y of Hero 1
        expected_hero4_pos = game.board.mirror_y(game.spawn_pos)
        assert hero4_pos == expected_hero4_pos, f"Hero 4 position {hero4_pos} must be Y-mirror of spawn {game.spawn_pos}"
        
        # Invariant 6: Hero 1 is current hero at turn 0
        assert game.turn == 0, "Game should start at turn 0"
        current = game.current_hero()
        assert current is not None, "Current hero should not be None"
        assert current.id == 1, "Hero 1 should be the current hero at turn 0"
        
        # Additional invariants from Game model
        assert game.status == Status.CREATED, "Initial game status should be CREATED"
        assert not game.finished, "Game should not be finished at initialization"
        assert game.training, "Default game should be in training mode"

    @given(
        map_choice=st.sampled_from(["small", "medium", "large"])
    )
    @settings(max_examples=15)
    def test_property_2_default_maps_initialization(self, map_choice):
        """
        Property 2: Default Maps Initialization
        For all default maps (small, medium, large), game initialization should satisfy
        all invariants and spawn positions should be valid air tiles.
        
        **Feature: vindinium-python-rewrite, Property 2: Default Maps Initialization**
        **Validates: Requirements 4.1, 3.7**
        """
        # Get the appropriate default map
        if map_choice == "small":
            map_str = Generator.get_default_map_small()
        elif map_choice == "medium":
            map_str = Generator.get_default_map_medium()
        else:
            map_str = Generator.get_default_map_large()
        
        board = MapParser.parse_map(map_str)
        game = Generator.create_initial_game_state(board, game_id=f"test-{map_choice}")
        
        # All invariants from Property 1
        assert len(game.heroes) == 4
        
        for hero in game.heroes:
            assert hero.life == Hero.MAX_LIFE
            assert hero.gold == 0
            # All spawn positions must be valid air tiles
            assert board.is_valid_position(hero.pos), f"Hero {hero.id} spawn position must be valid"
            assert board.is_air(hero.pos), f"Hero {hero.id} must spawn on air tile, not {board.get(hero.pos)}"
        
        # Unique positions
        positions = [hero.pos for hero in game.heroes]
        assert len(set(positions)) == 4
        
        # Current hero check
        assert game.current_hero().id == 1

    def test_hero_ids_are_sequential(self):
        """
        Test that hero IDs are sequential from 1 to 4.
        
        **Feature: vindinium-python-rewrite**
        **Validates: Requirement 1.4**
        """
        board = Generator.create_random_map(size=8, seed=123)
        game = Generator.create_initial_game_state(board, "test-ids")
        
        hero_ids = [hero.id for hero in game.heroes]
        assert hero_ids == [1, 2, 3, 4], "Hero IDs must be sequential 1-4"

    def test_hero_tokens_are_unique(self):
        """
        Test that all heroes have unique tokens.
        
        **Feature: vindinium-python-rewrite**
        **Validates: Requirement 1.4**
        """
        board = Generator.create_random_map(size=8, seed=456)
        game = Generator.create_initial_game_state(board, "test-tokens")
        
        tokens = [hero.token for hero in game.heroes]
        assert len(set(tokens)) == 4, "All hero tokens must be unique"

    @given(
        size=st.integers(min_value=6, max_value=12).filter(lambda x: x % 2 == 0)
    )
    @settings(max_examples=30)
    def test_property_3_spawn_positions_validity(self, size):
        """
        Property 3: Spawn Positions Validity
        For any valid board, all spawn positions must be valid positions on the board
        and must be air tiles (not walls, taverns, or mines).
        
        **Feature: vindinium-python-rewrite, Property 3: Spawn Positions Validity**
        **Validates: Requirement 4.1**
        """
        board = Generator.create_random_map(size=size, seed=size * 7)
        game = Generator.create_initial_game_state(board, f"test-access-{size}")
        
        for hero in game.heroes:
            # Spawn position must be within board bounds
            assert board.is_valid_position(hero.pos), f"Hero {hero.id} spawn at {hero.pos} must be valid position"
            
            # Spawn position must be air (heroes can't spawn on walls, taverns, or mines)
            assert board.is_air(hero.pos), f"Hero {hero.id} spawn at {hero.pos} must be air tile"

    def test_turn_cycling(self):
        """
        Test that current_hero cycles through heroes 1-4 correctly.
        
        **Feature: vindinium-python-rewrite**
        **Validates: Requirement 4.2**
        """
        board = Board([])  # Minimal board
        heroes = [
            Hero.create(i, f"Bot{i}", None, None, Pos(i, i), f"tok{i}")
            for i in range(1, 5)
        ]
        
        game = Game(
            id="test-cycle",
            training=True,
            board=board,
            hero1=heroes[0],
            hero2=heroes[1],
            hero3=heroes[2],
            hero4=heroes[3],
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Test turn cycling
        assert game.current_hero().id == 1  # Turn 0
        
        game = game.step()
        assert game.current_hero().id == 2  # Turn 1
        
        game = game.step()
        assert game.current_hero().id == 3  # Turn 2
        
        game = game.step()
        assert game.current_hero().id == 4  # Turn 3
        
        game = game.step()
        assert game.current_hero().id == 1  # Turn 4 (cycles back)

    @given(
        size=st.integers(min_value=6, max_value=16).filter(lambda x: x % 2 == 0),
        max_turns=st.integers(min_value=10, max_value=500)
    )
    @settings(max_examples=30)
    def test_property_4_game_parameters(self, size, max_turns):
        """
        Property 4: Game Parameters
        For any valid configuration, the game should respect the provided parameters
        (game_id, max_turns, training mode).
        
        **Feature: vindinium-python-rewrite, Property 4: Game Parameters**
        **Validates: Requirement 1.4**
        """
        board = Generator.create_random_map(size=size, seed=42)
        game_id = f"test-{size}-{max_turns}"
        
        game = Generator.create_initial_game_state(
            board,
            game_id=game_id,
            max_turns=max_turns,
            training=True
        )
        
        # Game parameters should match
        assert game.id == game_id
        assert game.max_turns == max_turns
        assert game.training
        assert not game.arena
        
        # Board should match
        assert game.board.size == size
        assert game.board.tiles == board.tiles

    def test_minimal_game_creation(self):
        """
        Test creating minimal test game for unit testing.
        
        **Feature: vindinium-python-rewrite**
        """
        game = Generator.create_minimal_test_game(size=6)
        
        assert game.id == "test-minimal"
        assert len(game.heroes) == 4
        assert game.board.size == 6
        
        # All initialization invariants should hold
        for hero in game.heroes:
            assert hero.life == Hero.MAX_LIFE
            assert hero.gold == 0
        
        positions = [hero.pos for hero in game.heroes]
        assert len(set(positions)) == 4


class TestGameStateHelpers:
    """Test helper methods for game state management."""

    def test_spawn_pos_of_calculation(self):
        """
        Test that spawn_pos_of correctly calculates mirrored positions for each hero.
        
        **Feature: vindinium-python-rewrite**
        **Validates: Requirement 3.7**
        """
        board = Generator.create_random_map(size=8, seed=999)
        game = Generator.create_initial_game_state(board, "test-spawn-calc")
        
        # Get a reference hero
        hero1 = game.hero1
        
        # Calculate expected positions using game method
        calculated_pos1 = game.spawn_pos_of(hero1)
        calculated_pos2 = game.spawn_pos_of(game.hero2)
        calculated_pos3 = game.spawn_pos_of(game.hero3)
        calculated_pos4 = game.spawn_pos_of(game.hero4)
        
        # Should match actual hero positions
        assert calculated_pos1 == hero1.pos
        assert calculated_pos2 == game.hero2.pos
        assert calculated_pos3 == game.hero3.pos
        assert calculated_pos4 == game.hero4.pos
        
        # Verify mirroring relationships
        assert calculated_pos2 == board.mirror_x(game.spawn_pos)
        assert calculated_pos3 == board.mirror_xy(game.spawn_pos)
        assert calculated_pos4 == board.mirror_y(game.spawn_pos)

    def test_game_immutability_on_creation(self):
        """
        Test that game creation produces immutable objects.
        
        **Feature: vindinium-python-rewrite**
        """
        board = Generator.create_random_map(size=6, seed=111)
        game1 = Generator.create_initial_game_state(board, "immutable-test-1")
        game2 = Generator.create_initial_game_state(board, "immutable-test-2")
        
        # Different game instances
        assert game1 is not game2
        assert game1.id != game2.id
        
        # But heroes should have same initial state (different instances)
        assert game1.hero1.life == game2.hero1.life == Hero.MAX_LIFE
        assert game1.hero1.gold == game2.hero1.gold == 0
