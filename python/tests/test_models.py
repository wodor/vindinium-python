"""Tests for core models."""

import pytest
from hypothesis import given, strategies as st
from vindinium.models import Pos, Dir, Tile, Hero, Board, Game, Status


class TestPos:
    """Test Position model."""

    def test_navigation(self):
        """Test movement in all directions."""
        pos = Pos(5, 5)
        assert pos.north() == Pos(4, 5)
        assert pos.south() == Pos(6, 5)
        assert pos.east() == Pos(5, 6)
        assert pos.west() == Pos(5, 4)

    def test_neighbors(self):
        """Test neighbor calculation."""
        pos = Pos(5, 5)
        neighbors = pos.neighbors()
        assert len(neighbors) == 4
        assert Pos(4, 5) in neighbors
        assert Pos(6, 5) in neighbors

    def test_is_in(self):
        """Test boundary checking."""
        assert Pos(0, 0).is_in(10)
        assert Pos(9, 9).is_in(10)
        assert not Pos(-1, 0).is_in(10)
        assert not Pos(10, 10).is_in(10)

    def test_move_to(self):
        """Test directional movement."""
        pos = Pos(5, 5)
        assert pos.move_to(Dir.NORTH) == Pos(4, 5)
        assert pos.move_to(Dir.STAY) == Pos(5, 5)

    def test_distance_and_adjacency(self):
        """Test distance calculation and adjacency."""
        pos1 = Pos(5, 5)
        pos2 = Pos(5, 6)  # Adjacent
        pos3 = Pos(7, 8)  # Distant
        
        assert pos1.distance_to(pos2) == 1
        assert pos1.distance_to(pos3) == 5  # |5-7| + |5-8| = 2 + 3 = 5
        assert pos1.is_adjacent_to(pos2)
        assert not pos1.is_adjacent_to(pos3)


class TestPosProperties:
    """Property-based tests for Position model."""

    @given(x=st.integers(), y=st.integers())
    def test_property_movement_north(self, x, y):
        """
        Property: Moving north decreases x coordinate by 1.
        Validates: Requirement 1.6 - North movement (x-1)
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.NORTH)
        assert moved == Pos(x - 1, y)
        assert moved.x == pos.x - 1
        assert moved.y == pos.y

    @given(x=st.integers(), y=st.integers())
    def test_property_movement_south(self, x, y):
        """
        Property: Moving south increases x coordinate by 1.
        Validates: Requirement 1.7 - South movement (x+1)
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.SOUTH)
        assert moved == Pos(x + 1, y)
        assert moved.x == pos.x + 1
        assert moved.y == pos.y

    @given(x=st.integers(), y=st.integers())
    def test_property_movement_east(self, x, y):
        """
        Property: Moving east increases y coordinate by 1.
        Validates: Requirement 1.8 - East movement (y+1)
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.EAST)
        assert moved == Pos(x, y + 1)
        assert moved.x == pos.x
        assert moved.y == pos.y + 1

    @given(x=st.integers(), y=st.integers())
    def test_property_movement_west(self, x, y):
        """
        Property: Moving west decreases y coordinate by 1.
        Validates: Requirement 1.9 - West movement (y-1)
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.WEST)
        assert moved == Pos(x, y - 1)
        assert moved.x == pos.x
        assert moved.y == pos.y - 1

    @given(x=st.integers(), y=st.integers())
    def test_property_movement_stay(self, x, y):
        """
        Property: STAY direction keeps position unchanged.
        Validates: Requirement 1.1 - Navigation support
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.STAY)
        assert moved == pos
        assert moved.x == x
        assert moved.y == y

    @given(x=st.integers(), y=st.integers())
    def test_property_navigation_reversibility_north_south(self, x, y):
        """
        Property: Moving North then South returns to original position.
        Validates: Navigation invariant - reversibility
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.NORTH).move_to(Dir.SOUTH)
        assert moved == pos

    @given(x=st.integers(), y=st.integers())
    def test_property_navigation_reversibility_south_north(self, x, y):
        """
        Property: Moving South then North returns to original position.
        Validates: Navigation invariant - reversibility
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.SOUTH).move_to(Dir.NORTH)
        assert moved == pos

    @given(x=st.integers(), y=st.integers())
    def test_property_navigation_reversibility_east_west(self, x, y):
        """
        Property: Moving East then West returns to original position.
        Validates: Navigation invariant - reversibility
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.EAST).move_to(Dir.WEST)
        assert moved == pos

    @given(x=st.integers(), y=st.integers())
    def test_property_navigation_reversibility_west_east(self, x, y):
        """
        Property: Moving West then East returns to original position.
        Validates: Navigation invariant - reversibility
        """
        pos = Pos(x, y)
        moved = pos.move_to(Dir.WEST).move_to(Dir.EAST)
        assert moved == pos

    @given(x=st.integers(min_value=-1000, max_value=-1), size=st.integers(min_value=1, max_value=100))
    def test_property_is_in_negative_x(self, x, size):
        """
        Property: Position with negative x is always out of bounds.
        Validates: Boundary checking - negative coordinates
        """
        pos = Pos(x, 0)
        assert not pos.is_in(size)

    @given(y=st.integers(min_value=-1000, max_value=-1), size=st.integers(min_value=1, max_value=100))
    def test_property_is_in_negative_y(self, y, size):
        """
        Property: Position with negative y is always out of bounds.
        Validates: Boundary checking - negative coordinates
        """
        pos = Pos(0, y)
        assert not pos.is_in(size)

    @given(size=st.integers(min_value=1, max_value=100))
    def test_property_is_in_exceeds_x(self, size):
        """
        Property: Position with x >= size is out of bounds.
        Validates: Boundary checking - upper bound x
        """
        pos = Pos(size, 0)
        assert not pos.is_in(size)
        pos_over = Pos(size + 1, 0)
        assert not pos_over.is_in(size)

    @given(size=st.integers(min_value=1, max_value=100))
    def test_property_is_in_exceeds_y(self, size):
        """
        Property: Position with y >= size is out of bounds.
        Validates: Boundary checking - upper bound y
        """
        pos = Pos(0, size)
        assert not pos.is_in(size)
        pos_over = Pos(0, size + 1)
        assert not pos_over.is_in(size)

    @given(
        x=st.integers(min_value=0, max_value=99),
        y=st.integers(min_value=0, max_value=99),
        size=st.integers(min_value=1, max_value=100)
    )
    def test_property_is_in_valid_bounds(self, x, y, size):
        """
        Property: Position with 0 <= x,y < size is within bounds.
        Validates: Boundary checking - valid coordinates
        """
        if x < size and y < size:
            pos = Pos(x, y)
            assert pos.is_in(size)

    @given(x=st.integers(), y=st.integers())
    def test_property_immutability(self, x, y):
        """
        Property: Moving a position creates a new instance (immutability).
        Validates: Constitutional requirement - immutability
        """
        pos = Pos(x, y)
        moved_north = pos.move_to(Dir.NORTH)
        moved_south = pos.move_to(Dir.SOUTH)
        moved_east = pos.move_to(Dir.EAST)
        moved_west = pos.move_to(Dir.WEST)
        
        # Original position unchanged
        assert pos.x == x
        assert pos.y == y
        
        # Each move creates a new instance
        assert pos is not moved_north
        assert pos is not moved_south
        assert pos is not moved_east
        assert pos is not moved_west


class TestTile:
    """Test Tile model."""

    def test_render(self):
        """Test tile rendering."""
        assert Tile.air().render() == "  "
        assert Tile.wall().render() == "##"
        assert Tile.tavern().render() == "[]"
        assert Tile.mine(None).render() == "$-"
        assert Tile.mine(1).render() == "$1"

    def test_parse(self):
        """Test tile parsing."""
        assert Tile.from_string("  ") == Tile.air()
        assert Tile.from_string("##") == Tile.wall()
        assert Tile.from_string("[]") == Tile.tavern()
        assert Tile.from_string("$-").owner is None
        assert Tile.from_string("$2").owner == 2

    def test_tile_properties(self):
        """Test tile property methods."""
        mine1 = Tile.mine(1)
        mine_neutral = Tile.mine(None)
        wall = Tile.wall()
        air = Tile.air()
        
        assert mine1.is_owned_by(1)
        assert not mine1.is_owned_by(2)
        assert mine_neutral.is_neutral_mine()
        assert not mine1.is_neutral_mine()
        
        assert air.is_passable()
        assert mine1.is_passable()
        assert not wall.is_passable()


class TestHero:
    """Test Hero model."""

    def test_create(self):
        """Test hero creation."""
        hero = Hero.create(1, "TestBot", "user123", 1200, Pos(0, 0), "abc")
        assert hero.id == 1
        assert hero.life == Hero.MAX_LIFE
        assert hero.gold == 0

    def test_drink_beer(self):
        """Test drinking beer."""
        hero = Hero.create(1, "Bot", None, None, Pos(0, 0), "abc")
        hero = hero.with_gold(10)
        
        hero_after = hero.drink_beer()
        assert hero_after.gold == 8  # -2 gold
        assert hero_after.life == 100  # Full life

    def test_life_bounds(self):
        """Test life clamping."""
        hero = Hero.create(1, "Bot", None, None, Pos(0, 0), "abc")
        
        # Can't exceed max
        hero_over = hero.with_life(50)
        assert hero_over.life == 100
        
        # Can't go below 0
        hero_under = hero.with_life(-200)
        assert hero_under.life == 0

    def test_hero_state_methods(self):
        """Test hero state checking methods."""
        hero = Hero.create(1, "Bot", None, None, Pos(0, 0), "abc")
        
        # Alive hero
        assert hero.is_alive()
        assert not hero.is_dead()
        assert not hero.needs_respawn()
        
        # Dead hero
        dead_hero = hero.with_life(-100)
        assert not dead_hero.is_alive()
        assert dead_hero.is_dead()
        assert dead_hero.needs_respawn()
        
        # Beer affordability
        poor_hero = hero.with_gold(1)
        rich_hero = hero.with_gold(10)
        assert not poor_hero.can_afford_beer()
        assert rich_hero.can_afford_beer()


class TestBoard:
    """Test Board model."""

    def test_size(self):
        """Test board size calculation."""
        tiles = [Tile.air() for _ in range(100)]
        board = Board(tiles)
        assert board.size == 10

    def test_pos_index_conversion(self):
        """Test position/index conversion."""
        tiles = [Tile.air() for _ in range(100)]
        board = Board(tiles)
        
        pos = Pos(3, 4)
        index = board.pos_to_index(pos)
        assert index == 34
        assert board.index_to_pos(index) == pos

    def test_update(self):
        """Test tile update."""
        tiles = [Tile.air() for _ in range(100)]
        board = Board(tiles)
        
        new_board = board.update(Pos(5, 5), Tile.wall())
        assert new_board.get(Pos(5, 5)) == Tile.wall()
        # Original unchanged
        assert board.get(Pos(5, 5)) == Tile.air()

    def test_board_queries(self):
        """Test board query methods."""
        tiles = [Tile.air() for _ in range(100)]
        tiles[55] = Tile.wall()  # Position (5, 5)
        tiles[66] = Tile.tavern()  # Position (6, 6)
        tiles[77] = Tile.mine(1)  # Position (7, 7)
        board = Board(tiles)
        
        assert board.is_air(Pos(0, 0))
        assert board.is_wall(Pos(5, 5))
        assert board.is_tavern(Pos(6, 6))
        assert board.is_mine(Pos(7, 7))
        
        assert board.is_passable(Pos(0, 0))  # Air is passable
        assert not board.is_passable(Pos(5, 5))  # Wall is not passable
        assert board.is_passable(Pos(6, 6))  # Tavern is passable
        
        assert board.is_valid_position(Pos(9, 9))
        assert not board.is_valid_position(Pos(10, 10))


class TestGame:
    """Test Game model."""

    def test_hero_access(self):
        """Test hero access methods."""
        board = Board([Tile.air() for _ in range(100)])
        heroes = [
            Hero.create(i, f"Bot{i}", None, None, Pos(i, i), f"tok{i}")
            for i in range(1, 5)
        ]
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=heroes[0],
            hero2=heroes[1],
            hero3=heroes[2],
            hero4=heroes[3],
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.CREATED,
        )
        
        assert len(game.heroes) == 4
        assert game.get_hero(2) == heroes[1]
        assert game.current_hero() == heroes[0]

    def test_step(self):
        """Test turn advancement."""
        board = Board([Tile.air() for _ in range(100)])
        heroes = [
            Hero.create(i, f"Bot{i}", None, None, Pos(i, i), f"tok{i}")
            for i in range(1, 5)
        ]
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=heroes[0],
            hero2=heroes[1],
            hero3=heroes[2],
            hero4=heroes[3],
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=10,
            status=Status.STARTED,
        )
        
        game2 = game.step()
        assert game2.turn == 1
        
        # Test turn max
        game_end = Game(
            id="test",
            training=True,
            board=board,
            hero1=heroes[0],
            hero2=heroes[1],
            hero3=heroes[2],
            hero4=heroes[3],
            spawn_pos=Pos(0, 0),
            turn=9,
            max_turns=10,
            status=Status.STARTED,
        )
        
        game_finished = game_end.step()
        assert game_finished.status == Status.TURN_MAX
        assert game_finished.finished

    def test_game_hero_queries(self):
        """Test game hero query methods."""
        board = Board([Tile.air() for _ in range(100)])
        heroes = [
            Hero.create(i, f"Bot{i}", None, None, Pos(i, i), f"tok{i}")
            for i in range(1, 5)
        ]
        # Make hero 2 dead and hero 3 crashed
        heroes[1] = heroes[1].with_life(-100)
        heroes[2] = heroes[2].set_timed_out()
        
        game = Game(
            id="test",
            training=True,
            board=board,
            hero1=heroes[0],
            hero2=heroes[1],
            hero3=heroes[2],
            hero4=heroes[3],
            spawn_pos=Pos(0, 0),
            turn=0,
            max_turns=100,
            status=Status.CREATED,
        )
        
        living = game.get_living_heroes()
        dead = game.get_dead_heroes()
        crashed = game.get_crashed_heroes()
        
        assert len(living) == 3  # Heroes 1, 3, 4 (hero 3 is crashed but alive)
        assert len(dead) == 1    # Hero 2
        assert len(crashed) == 1 # Hero 3
        
        # Test leaderboard (all have 0 gold initially)
        leaderboard = game.get_leaderboard()
        assert len(leaderboard) == 4

    def test_immutability(self):
        """Test that models are immutable and return new instances."""
        # Test Position immutability
        pos1 = Pos(5, 5)
        pos2 = pos1.north()
        assert pos1 == Pos(5, 5)  # Original unchanged
        assert pos2 == Pos(4, 5)  # New instance
        assert pos1 is not pos2
        
        # Test Hero immutability
        hero1 = Hero.create(1, "Bot", None, None, Pos(0, 0), "abc")
        hero2 = hero1.with_gold(10)
        assert hero1.gold == 0    # Original unchanged
        assert hero2.gold == 10   # New instance
        assert hero1 is not hero2
        
        # Test Board immutability
        board1 = Board([Tile.air() for _ in range(100)])
        board2 = board1.update(Pos(5, 5), Tile.wall())
        assert board1.get(Pos(5, 5)) == Tile.air()   # Original unchanged
        assert board2.get(Pos(5, 5)) == Tile.wall()  # New instance
        assert board1 is not board2
        
        # Test Game immutability
        game1 = Game(
            id="test", training=True, board=board1,
            hero1=hero1, hero2=hero1, hero3=hero1, hero4=hero1,
            spawn_pos=Pos(0, 0), turn=0, max_turns=100, status=Status.CREATED
        )
        game2 = game1.step()
        assert game1.turn == 0  # Original unchanged
        assert game2.turn == 1  # New instance
        assert game1 is not game2
