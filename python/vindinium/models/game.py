"""Game state model."""

from dataclasses import dataclass, replace
from typing import Optional
from .board import Board
from .hero import Hero
from .status import Status
from .pos import Pos


@dataclass
class Game:
    """Complete game state."""
    id: str
    training: bool
    board: Board
    hero1: Hero
    hero2: Hero
    hero3: Hero
    hero4: Hero
    spawn_pos: Pos
    turn: int
    max_turns: int
    status: Status

    @property
    def heroes(self) -> list[Hero]:
        """Get all heroes as a list."""
        return [self.hero1, self.hero2, self.hero3, self.hero4]

    @property
    def hero_id(self) -> int:
        """Get current hero ID (1-4)."""
        return (self.turn % 4) + 1

    def current_hero(self) -> Optional[Hero]:
        """Get the hero whose turn it is."""
        index = self.turn % 4
        return self.heroes[index] if index < len(self.heroes) else None

    def get_hero(self, id: int) -> Optional[Hero]:
        """Get hero by ID."""
        return next((h for h in self.heroes if h.id == id), None)

    def get_hero_at(self, pos: Pos) -> Optional[Hero]:
        """Get hero at position."""
        return next((h for h in self.heroes if h.pos == pos), None)

    def get_hero_by_token(self, token: str) -> Optional[Hero]:
        """Get hero by token."""
        return next((h for h in self.heroes if h.token == token), None)

    def get_hero_by_name(self, name: str) -> Optional[Hero]:
        """Get hero by name."""
        return next((h for h in self.heroes if h.name == name), None)

    def get_living_heroes(self) -> list[Hero]:
        """Get all living heroes."""
        return [h for h in self.heroes if h.is_alive()]

    def get_dead_heroes(self) -> list[Hero]:
        """Get all dead heroes."""
        return [h for h in self.heroes if h.is_dead()]

    def get_crashed_heroes(self) -> list[Hero]:
        """Get all crashed (timed out) heroes."""
        return [h for h in self.heroes if h.crashed]

    def current_hero_or_default(self) -> Hero:
        """Get current hero or first hero as default."""
        return self.current_hero() or self.hero1

    def step(self) -> "Game":
        """Advance to next turn."""
        if self.finished:
            return self
        
        next_game = replace(self, turn=self.turn + 1)
        if next_game.turn >= self.max_turns:
            return replace(next_game, status=Status.TURN_MAX)
        return next_game

    def set_timed_out(self) -> "Game":
        """Mark current hero as timed out."""
        hero = self.current_hero()
        if hero is None:
            return self
        
        game = self.with_hero(hero.set_timed_out())
        
        if game.training:
            return replace(game, status=Status.ALL_CRASHED)
        
        crashed_count = sum(1 for h in game.heroes if h.crashed)
        if crashed_count == 4:
            return replace(game, status=Status.ALL_CRASHED)
        
        return game

    @property
    def names(self) -> list[str]:
        """Get all hero names."""
        return [h.name for h in self.heroes]

    @property
    def has_many_names(self) -> bool:
        """Check if heroes have different names."""
        return len(set(self.names)) > 1

    def with_hero(self, hero: Hero) -> "Game":
        """Replace hero with updated version."""
        if hero.id == 1:
            return replace(self, hero1=hero)
        elif hero.id == 2:
            return replace(self, hero2=hero)
        elif hero.id == 3:
            return replace(self, hero3=hero)
        elif hero.id == 4:
            return replace(self, hero4=hero)
        return self

    def spawn_pos_of(self, hero: Hero) -> Pos:
        """Get spawn position for hero based on ID."""
        if hero.id == 1:
            return self.spawn_pos
        elif hero.id == 2:
            return self.board.mirror_x(self.spawn_pos)
        elif hero.id == 3:
            return self.board.mirror_xy(self.spawn_pos)
        else:  # hero.id == 4
            return self.board.mirror_y(self.spawn_pos)

    def with_training(self, training: bool) -> "Game":
        """Set training mode."""
        return replace(self, training=training)

    def with_board(self, board: Board) -> "Game":
        """Replace board."""
        return replace(self, board=board)

    def with_status(self, status: Status) -> "Game":
        """Set game status."""
        return replace(self, status=status)

    def with_turn(self, turn: int) -> "Game":
        """Set turn number."""
        return replace(self, turn=turn)

    def start(self) -> "Game":
        """Start the game."""
        return replace(self, status=Status.STARTED)

    @property
    def started(self) -> bool:
        """Check if game has started."""
        return self.status == Status.STARTED

    @property
    def finished(self) -> bool:
        """Check if game is finished."""
        return self.status.is_finished()

    @property
    def arena(self) -> bool:
        """Check if game is arena mode."""
        return not self.training

    def has_user_id(self, user_id: str) -> bool:
        """Check if user is in game."""
        return any(h.user_id == user_id for h in self.heroes)

    def get_winner(self) -> Optional[Hero]:
        """Get the hero with the most gold (winner)."""
        if not self.finished:
            return None
        return max(self.heroes, key=lambda h: h.gold)

    def get_leaderboard(self) -> list[Hero]:
        """Get heroes sorted by gold (descending)."""
        return sorted(self.heroes, key=lambda h: h.gold, reverse=True)

    def render(self) -> str:
        """Render game board."""
        return self.board.render()

    def __str__(self) -> str:
        return f"Game[{self.id}]: {self.status}, turn {self.turn}/{self.max_turns}"
