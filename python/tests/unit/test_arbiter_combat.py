"""Property-based tests for Arbiter combat mechanics."""

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from vindinium.models import Pos, Dir, Tile, TileType, Hero, Board, Game, Status
from vindinium.game_logic import Arbiter


# Test data generators
@st.composite
def game_with_adjacent_heroes(draw, size=6):
    """Generate a game state with two adjacent heroes."""
    # Create board with all air tiles
    board = Board([Tile.air() for _ in range(size * size)])
    
    # Generate attacker position
    attacker_x = draw(st.integers(min_value=1, max_value=size-2))
    attacker_y = draw(st.integers(min_value=1, max_value=size-2))
    attacker_pos = Pos(attacker_x, attacker_y)
    
    # Pick a direction for defender to be adjacent
    direction = draw(st.sampled_from([Dir.NORTH, Dir.SOUTH, Dir.EAST, Dir.WEST]))
    defender_pos = attacker_pos.move_to(direction)
    
    # Ensure defender position is valid
    assume(board.is_valid_position(defender_pos))
    
    # Generate defender with varied health
    defender_life = draw(st.integers(min_value=1, max_value=100))
    
    # Create attacker (Hero 1)
    attacker = Hero.create(
        id=1,
        name="Attacker",
        user_id="user1",
        elo=1200,
        pos=attacker_pos,
        token="token1"
    )
    
    # Create defender (Hero 2) with custom life
    defender = Hero.create(
        id=2,
        name="Defender",
        user_id="user2",
        elo=1200,
        pos=defender_pos,
        token="token2"
    )
    defender = defender.with_life(defender_life - defender.life)
    
    # Create other heroes at safe positions
    hero3 = Hero.create(3, "Bot3", "user3", 1200, Pos(0, 0), "token3")
    hero4 = Hero.create(4, "Bot4", "user4", 1200, Pos(0, 1), "token4")
    
    game = Game(
        id="combat-test",
        training=True,
        board=board,
        hero1=attacker,
        hero2=defender,
        hero3=hero3,
        hero4=hero4,
        spawn_pos=Pos(0, 0),
        turn=0,
        max_turns=100,
        status=Status.STARTED
    )
    
    return game, attacker, defender, direction


@st.composite
def game_with_mines_and_combat(draw, size=6):
    """Generate a game state with adjacent heroes where defender owns mines."""
    # Create board with some mines owned by defender
    tiles = [Tile.air() for _ in range(size * size)]
    
    # Add a few mines owned by defender (Hero 2)
    num_mines = draw(st.integers(min_value=1, max_value=min(5, size)))
    mine_positions = []
    for _ in range(num_mines):
        mine_x = draw(st.integers(min_value=0, max_value=size-1))
        mine_y = draw(st.integers(min_value=0, max_value=size-1))
        mine_pos = Pos(mine_x, mine_y)
        if mine_pos not in mine_positions:
            mine_positions.append(mine_pos)
            idx = mine_pos.x * size + mine_pos.y
            tiles[idx] = Tile.mine(2)  # Owned by Hero 2 (defender)
    
    board = Board(tiles)
    
    # Generate attacker and defender positions (adjacent)
    attacker_x = draw(st.integers(min_value=1, max_value=size-2))
    attacker_y = draw(st.integers(min_value=1, max_value=size-2))
    attacker_pos = Pos(attacker_x, attacker_y)
    
    direction = draw(st.sampled_from([Dir.NORTH, Dir.SOUTH, Dir.EAST, Dir.WEST]))
    defender_pos = attacker_pos.move_to(direction)
    
    # Ensure positions don't conflict with mines
    assume(board.is_valid_position(defender_pos))
    assume(board.get(attacker_pos).tile_type == TileType.AIR)
    assume(board.get(defender_pos).tile_type == TileType.AIR)
    
    # Defender has low health (will die from combat)
    defender_life = draw(st.integers(min_value=1, max_value=20))
    
    attacker = Hero.create(1, "Attacker", "user1", 1200, attacker_pos, "token1")
    defender = Hero.create(2, "Defender", "user2", 1200, defender_pos, "token2")
    defender = defender.with_life(defender_life - defender.life)
    
    hero3 = Hero.create(3, "Bot3", "user3", 1200, Pos(0, 0), "token3")
    hero4 = Hero.create(4, "Bot4", "user4", 1200, Pos(0, 1), "token4")
    
    game = Game(
        id="mine-transfer-test",
        training=True,
        board=board,
        hero1=attacker,
        hero2=defender,
        hero3=hero3,
        hero4=hero4,
        spawn_pos=Pos(0, 0),
        turn=0,
        max_turns=100,
        status=Status.STARTED
    )
    
    return game, attacker, defender, len(mine_positions)


class TestCombatInvariants:
    """Property-based tests for combat mechanics."""

    @given(game_data=game_with_adjacent_heroes())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_combat_defender_takes_damage(self, game_data):
        """
        Property: Defender takes damage in combat
        When heroes are adjacent, the defender loses exactly 20 health.
        **Feature: vindinium-python-rewrite, Property: Combat damage**
        **Validates: Requirement 6.2**
        """
        game, attacker, defender, direction = game_data
        
        # Ensure defender is alive before combat
        assume(defender.is_alive())
        # Skip edge case where defender ends up with exactly 0 HP after finalize_turn
        # (21 - 20 - 1 = 0, but respawn already happened)
        assume(defender.life != 21)
        
        # Store original state
        original_attacker_life = attacker.life
        original_defender_life = defender.life
        
        # Process move (STAY) to trigger combat without movement
        result_game = Arbiter.process_move(game, attacker.id, Dir.STAY)
        
        # Get updated heroes
        updated_attacker = result_game.get_hero(attacker.id)
        updated_defender = result_game.get_hero(defender.id)
        
        assert updated_attacker is not None
        assert updated_defender is not None
        
        # Attacker health should NOT change (only defenders take damage)
        # However, finalize_turn applies -1 life drain to all living heroes
        expected_attacker_life = max(0, original_attacker_life - 1)
        assert updated_attacker.life == expected_attacker_life
        
        # Defender should take 20 damage from combat, plus -1 from life drain if alive
        if original_defender_life > 20:
            # Defender survives: -20 from combat, -1 from life drain
            expected_defender_life = original_defender_life - 20 - 1
        else:
            # Defender dies: life goes to 0, then respawns with 100, then -1 from drain
            expected_defender_life = 99
        
        assert updated_defender.life == expected_defender_life

    @given(game_data=game_with_adjacent_heroes())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_attacker_health_unchanged_by_combat(self, game_data):
        """
        Property: Attacker health unchanged by combat
        The attacking hero's health should not change due to combat itself
        (only life drain applies).
        **Feature: vindinium-python-rewrite, Property: Attacker immunity**
        **Validates: Requirement 6.1, 6.2**
        """
        game, attacker, defender, direction = game_data
        
        # Store original attacker health
        original_attacker_life = attacker.life
        
        # Process move
        result_game = Arbiter.process_move(game, attacker.id, Dir.STAY)
        
        # Get updated attacker
        updated_attacker = result_game.get_hero(attacker.id)
        assert updated_attacker is not None
        
        # Attacker should only lose 1 life from finalize_turn drain
        expected_life = max(0, original_attacker_life - 1)
        assert updated_attacker.life == expected_life

    @given(game_data=game_with_adjacent_heroes())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_defender_death_and_respawn(self, game_data):
        """
        Property: Defender death and respawn
        When a defender's health reaches 0, they should respawn at spawn position
        with 100 health.
        **Feature: vindinium-python-rewrite, Property: Respawn mechanics**
        **Validates: Requirement 6.3**
        """
        game, attacker, defender, direction = game_data
        
        # Only test when defender will die from combat
        assume(defender.life <= 20)
        
        # Store spawn position
        spawn_pos = game.spawn_pos_of(defender)
        
        # Process move
        result_game = Arbiter.process_move(game, attacker.id, Dir.STAY)
        
        # Get updated defender
        updated_defender = result_game.get_hero(defender.id)
        assert updated_defender is not None
        
        # Defender should have respawned
        assert updated_defender.pos == spawn_pos
        # After respawn, hero gets 100 life, then -1 from finalize_turn
        assert updated_defender.life == 99

    @given(game_data=game_with_mines_and_combat())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_mine_transfer_on_death(self, game_data):
        """
        Property: Mine transfer on defender death
        When a defender dies, all their mines should be transferred to the attacker.
        **Feature: vindinium-python-rewrite, Property: Mine transfer**
        **Validates: Requirement 6.3**
        """
        game, attacker, defender, num_defender_mines = game_data
        
        # Only test when defender will die
        assume(defender.life <= 20)
        
        # Count mines owned by defender before combat
        defender_mines_before = sum(
            1 for tile in game.board.tiles 
            if tile.tile_type == TileType.MINE and tile.owner == defender.id
        )
        assert defender_mines_before > 0  # Ensure defender has mines
        
        # Process move
        result_game = Arbiter.process_move(game, attacker.id, Dir.STAY)
        
        # Count mines after combat
        attacker_mines_after = sum(
            1 for tile in result_game.board.tiles 
            if tile.tile_type == TileType.MINE and tile.owner == attacker.id
        )
        defender_mines_after = sum(
            1 for tile in result_game.board.tiles 
            if tile.tile_type == TileType.MINE and tile.owner == defender.id
        )
        
        # All defender's mines should have been transferred to attacker
        assert defender_mines_after == 0
        assert attacker_mines_after == defender_mines_before

    @given(game_data=game_with_adjacent_heroes())
    @settings(suppress_health_check=[HealthCheck.large_base_example], max_examples=50)
    def test_property_combat_only_occurs_when_adjacent(self, game_data):
        """
        Property: Combat only occurs when adjacent
        Combat should only trigger when heroes are exactly 1 tile apart.
        **Feature: vindinium-python-rewrite, Property: Adjacency requirement**
        **Validates: Requirement 6.1**
        """
        game, attacker, defender, direction = game_data
        
        # Verify heroes are adjacent
        assert attacker.pos.is_adjacent_to(defender.pos)
        
        original_defender_life = defender.life
        
        # Process move
        result_game = Arbiter.process_move(game, attacker.id, Dir.STAY)
        
        updated_defender = result_game.get_hero(defender.id)
        assert updated_defender is not None
        
        # Defender should have taken combat damage
        # Combat damage is 20, life drain is 1, total 21
        # If hero dies from combat (life <= 20), they respawn with 100 and then take -1 drain = 99
        # If hero dies from life drain (life == 21), they respawn with 100 and no more drain
        # If hero survives (life > 21), they take 21 damage total
        if original_defender_life > 21:
            # Survived: took 20 combat damage + 1 life drain
            assert updated_defender.life == original_defender_life - 21
        elif original_defender_life == 21:
            # Died from life drain after combat: respawned with full health, no more drain
            assert updated_defender.life == 100
            assert updated_defender.pos == game.spawn_pos_of(defender)
        else:
            # Died from combat: respawned with 100, then took -1 life drain = 99
            assert updated_defender.life == 99
            assert updated_defender.pos == game.spawn_pos_of(defender)


class TestCombatEdgeCases:
    """Test specific edge cases for combat mechanics."""
    
    def test_combat_exact_20_damage(self):
        """Test that combat deals exactly 20 damage."""
        # Create simple board
        board = Board([Tile.air() for _ in range(16)])
        
        # Hero 1 at (1, 1), Hero 2 at (1, 2) - adjacent
        hero1 = Hero.create(1, "Attacker", "user1", 1200, Pos(1, 1), "token1")
        hero2 = Hero.create(2, "Defender", "user2", 1200, Pos(1, 2), "token2")
        # Set defender to 50 health
        hero2 = hero2.with_life(-50)
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero1,
            hero2=hero2,
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(0, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(0, 1), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Process move (STAY to trigger combat without movement)
        result = Arbiter.process_move(game, 1, Dir.STAY)
        
        updated_hero1 = result.get_hero(1)
        updated_hero2 = result.get_hero(2)
        
        assert updated_hero1 is not None
        assert updated_hero2 is not None
        
        # Hero 1 should only lose 1 from life drain
        assert updated_hero1.life == 99
        
        # Hero 2 should lose 20 from combat + 1 from life drain = 21
        assert updated_hero2.life == 50 - 21  # 29
    
    def test_combat_defender_at_20_health_dies(self):
        """Test that defender with exactly 20 health dies from combat."""
        board = Board([Tile.air() for _ in range(16)])
        
        hero1 = Hero.create(1, "Attacker", "user1", 1200, Pos(1, 1), "token1")
        hero2 = Hero.create(2, "Defender", "user2", 1200, Pos(1, 2), "token2")
        # Set defender to exactly 20 health
        hero2 = hero2.with_life(-80)
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero1,
            hero2=hero2,
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(0, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(0, 1), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Hero 2's spawn position is mirror_x of Pos(0, 0) = Pos(3, 0) for 4x4 board
        hero2_spawn = game.board.mirror_x(Pos(0, 0))
        
        # Process move
        result = Arbiter.process_move(game, 1, Dir.STAY)
        
        updated_hero2 = result.get_hero(2)
        assert updated_hero2 is not None
        
        # Hero 2 should have died and respawned
        assert updated_hero2.life == 99  # Respawned with 100, -1 from drain
        assert updated_hero2.pos == hero2_spawn  # Spawn position
    
    def test_no_combat_when_not_adjacent(self):
        """Test that no combat occurs when heroes are not adjacent."""
        board = Board([Tile.air() for _ in range(25)])  # 5x5 board
        
        # Heroes far apart
        hero1 = Hero.create(1, "Hero1", "user1", 1200, Pos(0, 0), "token1")
        hero2 = Hero.create(2, "Hero2", "user2", 1200, Pos(3, 3), "token2")
        hero3 = Hero.create(3, "Bot3", "user3", 1200, Pos(1, 0), "token3")
        hero4 = Hero.create(4, "Bot4", "user4", 1200, Pos(2, 0), "token4")
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero1,
            hero2=hero2,
            hero3=hero3,
            hero4=hero4,
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Process move
        result = Arbiter.process_move(game, 1, Dir.STAY)
        
        updated_hero1 = result.get_hero(1)
        updated_hero2 = result.get_hero(2)
        
        assert updated_hero1 is not None
        assert updated_hero2 is not None
        
        # Both heroes should only lose 1 from life drain (no combat)
        assert updated_hero1.life == 99
        assert updated_hero2.life == 99
    
    def test_mine_transfer_multiple_mines(self):
        """Test that all defender's mines transfer to attacker."""
        # Create board with 3 mines owned by Hero 2
        tiles = [Tile.air() for _ in range(25)]  # 5x5
        tiles[0] = Tile.mine(2)  # (0, 0)
        tiles[5] = Tile.mine(2)  # (1, 0)
        tiles[10] = Tile.mine(2)  # (2, 0)
        board = Board(tiles)
        
        # Adjacent heroes
        hero1 = Hero.create(1, "Attacker", "user1", 1200, Pos(2, 2), "token1")
        hero2 = Hero.create(2, "Defender", "user2", 1200, Pos(2, 3), "token2")
        # Set defender to low health
        hero2 = hero2.with_life(-90)  # 10 health
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=hero1,
            hero2=hero2,
            hero3=Hero.create(3, "Bot3", "user3", 1200, Pos(3, 0), "token3"),
            hero4=Hero.create(4, "Bot4", "user4", 1200, Pos(4, 0), "token4"),
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.STARTED
        )
        
        # Verify defender has 3 mines
        defender_mines_before = sum(
            1 for tile in game.board.tiles
            if tile.tile_type == TileType.MINE and tile.owner == 2
        )
        assert defender_mines_before == 3
        
        # Process move (combat will kill defender)
        result = Arbiter.process_move(game, 1, Dir.STAY)
        
        # All 3 mines should now belong to attacker
        attacker_mines = sum(
            1 for tile in result.board.tiles
            if tile.tile_type == TileType.MINE and tile.owner == 1
        )
        defender_mines = sum(
            1 for tile in result.board.tiles
            if tile.tile_type == TileType.MINE and tile.owner == 2
        )
        
        assert attacker_mines == 3
        assert defender_mines == 0
