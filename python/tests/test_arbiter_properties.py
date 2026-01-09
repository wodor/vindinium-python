"""Property-based tests for Arbiter movement mechanics."""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from vindinium.models import Pos, Dir, Tile, TileType, Hero, Board, Game, Status
from vindinium.game_logic import Arbiter
from vindinium.system.generator import Generator


# Test data generators
@st.composite
def simple_game_state(draw, size=6):
    """Generate simple game state for testing."""
    # Create board with all air tiles
    board = Board([Tile.air() for _ in range(size * size)])
    
    # Generate 4 heroes at different positions
    positions = []
    for i in range(4):
        x = draw(st.integers(min_value=0, max_value=size-1))
        y = draw(st.integers(min_value=0, max_value=size-1))
        pos = Pos(x, y)
        # Ensure unique positions
        while pos in positions:
            x = draw(st.integers(min_value=0, max_value=size-1))
            y = draw(st.integers(min_value=0, max_value=size-1))
            pos = Pos(x, y)
        positions.append(pos)
    
    heroes = []
    for i in range(4):
        hero = Hero.create(
            id=i+1,
            name=f"TestBot{i+1}",
            user_id=f"user{i+1}",
            elo=1200,
            pos=positions[i],
            token=f"token{i+1}"
        )
        heroes.append(hero)
    
    return Game(
        id="test-game",
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


class TestMovementProperties:
    """Property-based tests for movement mechanics."""

    @given(
        game=simple_game_state(),
        direction=st.sampled_from([Dir.NORTH, Dir.SOUTH, Dir.EAST, Dir.WEST, Dir.STAY])
    )
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_6_movement_to_empty_space(self, game, direction):
        """
        Property 6: Movement to Empty Space
        For any game state and hero, when the hero moves to an empty (Air) tile,
        the hero's position should be updated to the target position and no other
        game state should change.
        **Feature: vindinium-python-rewrite, Property 6: Movement to Empty Space**
        **Validates: Requirements 2.1**
        """
        # Get current hero
        hero = game.current_hero()
        assume(hero is not None and hero.is_alive() and not hero.crashed)
        
        # Calculate target position
        target_pos = hero.pos.move_to(direction)
        
        # Only test if target is valid and empty
        assume(game.board.is_valid_position(target_pos))
        assume(game.board.is_air(target_pos))
        assume(game.get_hero_at(target_pos) is None)  # No hero collision
        
        # Store original state
        original_hero = hero
        original_board = game.board
        original_other_heroes = [h for h in game.heroes if h.id != hero.id]
        
        # Process the move
        result_game = Arbiter.process_move(game, hero.id, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(hero.id)
        assert updated_hero is not None
        
        # Hero position should be updated to target
        if direction == Dir.STAY:
            assert updated_hero.pos == original_hero.pos
        else:
            assert updated_hero.pos == target_pos
        
        # Board should remain unchanged (no tile modifications for air movement)
        assert result_game.board.tiles == original_board.tiles
        
        # Other heroes should remain unchanged (position-wise, ignoring life/gold changes from turn effects)
        for original_other in original_other_heroes:
            updated_other = result_game.get_hero(original_other.id)
            assert updated_other is not None
            # Position should be same (no combat assumed in this test)
            assert updated_other.pos == original_other.pos

    @given(
        size=st.integers(min_value=4, max_value=6),
        direction=st.sampled_from([Dir.NORTH, Dir.SOUTH, Dir.EAST, Dir.WEST])
    )
    @settings(max_examples=50)
    def test_property_7_wall_collision_handling(self, size, direction):
        """
        Property 7: Wall Collision Handling
        For any game state and hero, when the hero attempts to move into a wall tile,
        the hero's position should remain unchanged and no other game state should change.
        **Feature: vindinium-python-rewrite, Property 7: Wall Collision Handling**
        **Validates: Requirements 2.2**
        """
        # Create simple game state
        board = Board([Tile.air() for _ in range(size * size)])
        hero_pos = Pos(size // 2, size // 2)
        target_pos = hero_pos.move_to(direction)
        
        # Only test if target is valid
        assume(board.is_valid_position(target_pos))
        
        # Place a wall at target position
        wall_board = board.update(target_pos, Tile.wall())
        
        hero = Hero.create(1, "TestBot", "user1", 1200, hero_pos, "token1")
        
        game = Game(
            id="wall-test",
            training=True,
            board=wall_board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(0, 1), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(1, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Store original state
        original_hero_pos = hero.pos
        original_board = game.board
        
        # Process the move
        result_game = Arbiter.process_move(game, 1, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(1)
        assert updated_hero is not None
        
        # Hero position should remain unchanged
        assert updated_hero.pos == original_hero_pos
        
        # Board should remain unchanged
        assert result_game.board.tiles == original_board.tiles

    @given(
        size=st.integers(min_value=4, max_value=6),
        direction=st.sampled_from([Dir.NORTH, Dir.SOUTH, Dir.EAST, Dir.WEST])
    )
    @settings(max_examples=50)
    def test_property_8_hero_collision_prevention(self, size, direction):
        """
        Property 8: Hero Collision Prevention
        For any game state where two heroes would occupy the same position after movement,
        both heroes should remain at their original positions.
        **Feature: vindinium-python-rewrite, Property 8: Hero Collision Prevention**
        **Validates: Requirements 2.3**
        """
        # Create board with all air tiles
        board = Board([Tile.air() for _ in range(size * size)])
        
        # Create two heroes at adjacent positions
        hero1_pos = Pos(size // 2, size // 2)
        hero2_pos = hero1_pos.move_to(direction)
        
        # Skip if hero2 position is out of bounds
        assume(board.is_valid_position(hero2_pos))
        
        hero1 = Hero.create(1, "Bot1", "user1", 1200, hero1_pos, "token1")
        hero2 = Hero.create(2, "Bot2", "user2", 1200, hero2_pos, "token2")
        hero3 = Hero.create(3, "Bot3", "user3", 1200, Pos(0, 0), "token3")
        hero4 = Hero.create(4, "Bot4", "user4", 1200, Pos(0, 1), "token4")
        
        game = Game(
            id="collision-test",
            training=True,
            board=board,
            hero1=hero1,
            hero2=hero2,
            hero3=hero3,
            hero4=hero4,
            spawn_pos=Pos(0, 0),
            turn=0,  # Hero 1's turn
            max_turns=100,
            status=Status.STARTED
        )
        
        # Store original positions
        original_hero1_pos = hero1.pos
        original_hero2_pos = hero2.pos
        
        # Hero 1 tries to move toward hero 2's position
        result_game = Arbiter.process_move(game, 1, direction)
        
        # Get updated heroes
        updated_hero1 = result_game.get_hero(1)
        updated_hero2 = result_game.get_hero(2)
        
        assert updated_hero1 is not None
        assert updated_hero2 is not None
        
        # Hero 1 should stay in original position (collision prevented)
        assert updated_hero1.pos == original_hero1_pos
        
        # Hero 2 should remain in original position
        assert updated_hero2.pos == original_hero2_pos


# Additional helper tests to ensure the test setup is working
class TestMovementTestHelpers:
    """Test the test helpers and generators."""
    
    def test_simple_movement_scenario(self):
        """Test a simple movement scenario to verify Arbiter works."""
        # Create simple 4x4 board with all air
        board = Board([Tile.air() for _ in range(16)])
        hero = Hero.create(1, "TestBot", "user1", 1200, Pos(1, 1), "token1")
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(2, 2), "token3"),  # Moved away from collision
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(1, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Move hero north
        result = Arbiter.process_move(game, 1, Dir.NORTH)
        updated_hero = result.get_hero(1)
        
        assert updated_hero is not None
        assert updated_hero.pos == Pos(0, 1)  # Moved north
    
    def test_wall_collision_scenario(self):
        """Test wall collision scenario to verify Arbiter works."""
        # Create board with wall at (0, 1)
        tiles = [Tile.air() for _ in range(16)]
        tiles[1] = Tile.wall()  # Position (0, 1)
        board = Board(tiles)
        
        hero = Hero.create(1, "TestBot", "user1", 1200, Pos(1, 1), "token1")
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(2, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(2, 1), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Try to move hero north into wall
        result = Arbiter.process_move(game, 1, Dir.NORTH)
        updated_hero = result.get_hero(1)
        
        assert updated_hero is not None
        assert updated_hero.pos == Pos(1, 1)  # Should stay in place