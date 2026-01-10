"""Property-based tests for Arbiter tavern mechanics."""

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from vindinium.models import Pos, Dir, Tile, Hero, Board, Game, Status
from vindinium.game_logic import Arbiter


# Test data generators
@st.composite
def game_with_tavern(draw, size=6):
    """Generate a game state with a tavern at a specific position."""
    # Create board with all air tiles
    tiles = [Tile.air() for _ in range(size * size)]
    
    # Generate hero position
    hero_x = draw(st.integers(min_value=0, max_value=size-1))
    hero_y = draw(st.integers(min_value=0, max_value=size-1))
    hero_pos = Pos(hero_x, hero_y)
    
    # Pick a direction to place the tavern
    direction = draw(st.sampled_from([Dir.NORTH, Dir.SOUTH, Dir.EAST, Dir.WEST]))
    tavern_pos = hero_pos.move_to(direction)
    
    # Ensure tavern is in bounds
    assume(0 <= tavern_pos.x < size)
    assume(0 <= tavern_pos.y < size)
    
    # Place tavern at target position
    # Note: Board uses row-major indexing: pos.x * size + pos.y
    # where x is the row and y is the column
    tavern_index = tavern_pos.x * size + tavern_pos.y
    tiles[tavern_index] = Tile.tavern()
    
    board = Board(tiles)
    
    # Generate hero with varied resources
    life = draw(st.integers(min_value=1, max_value=100))
    gold = draw(st.integers(min_value=0, max_value=10))
    
    hero = Hero.create(
        id=1,
        name="TestBot",
        user_id="user1",
        elo=1200,
        pos=hero_pos,
        token="token1"
    )
    # Set custom life and gold
    hero = hero.with_life(life - hero.life).with_gold(gold)
    
    # Create other heroes at different positions
    other_heroes = []
    for i in range(2, 5):
        other_pos = Pos((i-1) % size, i % size)
        if other_pos != hero_pos and other_pos != tavern_pos:
            other_heroes.append(
                Hero.create(i, f"Bot{i}", f"user{i}", 1200, other_pos, f"token{i}")
            )
        else:
            # Fallback positions
            other_heroes.append(
                Hero.create(i, f"Bot{i}", f"user{i}", 1200, Pos(0, i-2), f"token{i}")
            )
    
    game = Game(
        id="tavern-test",
        training=True,
        board=board,
        hero1=hero,
        hero2=other_heroes[0],
        hero3=other_heroes[1],
        hero4=other_heroes[2],
        spawn_pos=Pos(0, 0),
        turn=0,
        max_turns=100,
        status=Status.STARTED
    )
    
    return game, hero, tavern_pos, direction


class TestTavernInvariants:
    """Property-based tests for tavern mechanics."""

    @given(game_data=game_with_tavern())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_tavern_with_sufficient_gold(self, game_data):
        """
        Property: Tavern with sufficient gold (>=2)
        When a hero with gold >= 2 moves into a tavern, they should:
        - Move to the tavern position
        - Lose 2 gold
        - Gain 50 health (capped at 100), then -1 from daily life drain
        **Feature: vindinium-python-rewrite, Property: Tavern with sufficient gold**
        **Validates: Requirements 8.1, 8.3**
        """
        game, hero, tavern_pos, direction = game_data
        
        # Only test heroes with sufficient gold
        assume(hero.can_afford_beer())
        assert hero.gold >= 2
        
        # Store original state
        original_life = hero.life
        original_gold = hero.gold
        original_pos = hero.pos
        
        # Process the move toward tavern
        result_game = Arbiter.process_move(game, hero.id, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(hero.id)
        assert updated_hero is not None
        
        # Hero should have moved to tavern
        assert updated_hero.pos == tavern_pos
        
        # Gold should decrease by 2
        assert updated_hero.gold == original_gold - 2
        
        # Life should increase by 50, capped at 100, then -1 from finalize_turn
        expected_life_before_drain = min(100, original_life + 50)
        expected_life = expected_life_before_drain - 1
        assert updated_hero.life == expected_life
        
        # Gold must not drop below 0
        assert updated_hero.gold >= 0
        
        # Life must not exceed 100
        assert updated_hero.life <= 100

    @given(game_data=game_with_tavern())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_tavern_without_sufficient_gold(self, game_data):
        """
        Property: Tavern without sufficient gold (<2)
        When a hero with gold < 2 attempts to move into a tavern, they should:
        - Stay at their original position
        - Keep all their gold
        - Maintain their health
        **Feature: vindinium-python-rewrite, Property: Tavern without sufficient gold**
        **Validates: Requirements 8.2**
        """
        game, hero, tavern_pos, direction = game_data
        
        # Only test heroes without sufficient gold
        assume(not hero.can_afford_beer())
        assert hero.gold < 2
        
        # Store original state
        original_life = hero.life
        original_gold = hero.gold
        original_pos = hero.pos
        
        # Process the move toward tavern
        result_game = Arbiter.process_move(game, hero.id, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(hero.id)
        assert updated_hero is not None
        
        # Hero should NOT have moved (stays in original position)
        assert updated_hero.pos == original_pos
        
        # Gold should remain unchanged
        assert updated_hero.gold == original_gold
        
        # Gold must not drop below 0
        assert updated_hero.gold >= 0

    @given(game_data=game_with_tavern())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_health_cap_at_100(self, game_data):
        """
        Property: Health capped at 100
        When a hero drinks beer, their health should never exceed 100.
        **Feature: vindinium-python-rewrite, Property: Health capped at 100**
        **Validates: Requirements 8.3**
        """
        game, hero, tavern_pos, direction = game_data
        
        # Only test heroes with sufficient gold
        assume(hero.can_afford_beer())
        
        # Store original state
        original_life = hero.life
        
        # Process the move toward tavern
        result_game = Arbiter.process_move(game, hero.id, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(hero.id)
        assert updated_hero is not None
        
        # Health must be capped at 100 (even after -1 from finalize_turn)
        assert updated_hero.life <= 100
        
        # If hero had > 50 health, they should cap at 100, then -1 from drain = 99
        if original_life > 50:
            assert updated_hero.life == 99

    @given(game_data=game_with_tavern())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_gold_never_negative(self, game_data):
        """
        Property: Gold never negative
        Hero gold must never drop below 0 in any circumstance.
        **Feature: vindinium-python-rewrite, Property: Gold never negative**
        **Validates: Hero invariant - gold >= 0**
        """
        game, hero, tavern_pos, direction = game_data
        
        # Process the move toward tavern
        result_game = Arbiter.process_move(game, hero.id, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(hero.id)
        assert updated_hero is not None
        
        # Gold must NEVER be negative
        assert updated_hero.gold >= 0

    @given(game_data=game_with_tavern())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_insufficient_gold_state_preservation(self, game_data):
        """
        Property: State preservation when insufficient gold
        When a hero cannot afford beer, their entire state (except turn effects)
        should remain unchanged.
        **Feature: vindinium-python-rewrite, Property: State preservation**
        **Validates: Requirements 8.2**
        """
        game, hero, tavern_pos, direction = game_data
        
        # Only test heroes without sufficient gold
        assume(not hero.can_afford_beer())
        
        # Store original state
        original_pos = hero.pos
        original_gold = hero.gold
        
        # Process the move toward tavern
        result_game = Arbiter.process_move(game, hero.id, direction)
        
        # Get updated hero
        updated_hero = result_game.get_hero(hero.id)
        assert updated_hero is not None
        
        # Position must be unchanged
        assert updated_hero.pos == original_pos
        
        # Gold must be unchanged
        assert updated_hero.gold == original_gold


class TestTavernEdgeCases:
    """Test specific edge cases for tavern mechanics."""
    
    def test_tavern_exactly_2_gold(self):
        """Test that exactly 2 gold is sufficient to drink beer."""
        # Create simple board with tavern
        tiles = [Tile.air() for _ in range(16)]
        tiles[5] = Tile.tavern()  # Position (1, 1)
        board = Board(tiles)
        
        # Hero at (1, 0) with exactly 2 gold and low health
        hero = Hero.create(1, "TestBot", "user1", 1200, Pos(1, 0), "token1")
        hero = hero.with_life(-80).with_gold(2)  # 20 health, 2 gold
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(2, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(3, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Move east into tavern (1,0) -> (1,1)
        result = Arbiter.process_move(game, 1, Dir.EAST)
        updated_hero = result.get_hero(1)
        
        assert updated_hero is not None
        assert updated_hero.pos == Pos(1, 1)  # Moved to tavern
        assert updated_hero.gold == 0  # 2 - 2 = 0
        # Life: 20 + 50 = 70, then -1 from finalize_turn = 69
        assert updated_hero.life == 69
    
    def test_tavern_1_gold_insufficient(self):
        """Test that 1 gold is not sufficient to drink beer."""
        # Create simple board with tavern
        tiles = [Tile.air() for _ in range(16)]
        tiles[5] = Tile.tavern()  # Position (1, 1)
        board = Board(tiles)
        
        # Hero at (1, 0) with only 1 gold
        hero = Hero.create(1, "TestBot", "user1", 1200, Pos(1, 0), "token1")
        hero = hero.with_life(-50).with_gold(1)  # 50 health, 1 gold
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(2, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(3, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Try to move east into tavern
        result = Arbiter.process_move(game, 1, Dir.EAST)
        updated_hero = result.get_hero(1)
        
        assert updated_hero is not None
        assert updated_hero.pos == Pos(1, 0)  # Should stay in place
        assert updated_hero.gold == 1  # Gold unchanged
        # Life: 50 - 1 from finalize_turn = 49
        assert updated_hero.life == 49
    
    def test_tavern_health_already_at_100(self):
        """Test drinking beer when health is already at 100."""
        # Create simple board with tavern
        tiles = [Tile.air() for _ in range(16)]
        tiles[5] = Tile.tavern()  # Position (1, 1)
        board = Board(tiles)
        
        # Hero at (1, 0) with full health and enough gold
        hero = Hero.create(1, "TestBot", "user1", 1200, Pos(1, 0), "token1")
        hero = hero.with_gold(5)  # 100 health (default), 5 gold
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(2, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(3, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Move east into tavern
        result = Arbiter.process_move(game, 1, Dir.EAST)
        updated_hero = result.get_hero(1)
        
        assert updated_hero is not None
        assert updated_hero.pos == Pos(1, 1)  # Moved to tavern
        assert updated_hero.gold == 3  # 5 - 2 = 3
        # Life: 100 + 50 = 150, capped at 100, then -1 from finalize_turn = 99
        assert updated_hero.life == 99
    
    def test_tavern_health_at_51(self):
        """Test drinking beer when health is exactly 51 (edge of cap)."""
        # Create simple board with tavern
        tiles = [Tile.air() for _ in range(16)]
        tiles[5] = Tile.tavern()  # Position (1, 1)
        board = Board(tiles)
        
        # Hero at (1, 0) with 51 health and enough gold
        hero = Hero.create(1, "TestBot", "user1", 1200, Pos(1, 0), "token1")
        hero = hero.with_life(-49).with_gold(5)  # 51 health, 5 gold
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero,
            hero2=Hero.create(2, "Bot2", "user2", 1200, Pos(0, 0), "token2"),
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(2, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(3, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Move east into tavern
        result = Arbiter.process_move(game, 1, Dir.EAST)
        updated_hero = result.get_hero(1)
        
        assert updated_hero is not None
        assert updated_hero.pos == Pos(1, 1)  # Moved to tavern
        assert updated_hero.gold == 3  # 5 - 2 = 3
        # Life: 51 + 50 = 101, capped at 100, then -1 from finalize_turn = 99
        assert updated_hero.life == 99
