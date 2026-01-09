"""Hero model."""

from dataclasses import dataclass, replace
from typing import Optional
from .pos import Pos, Dir


@dataclass
class Hero:
    """A hero in the game."""
    id: int
    token: str
    name: str
    user_id: Optional[str]
    elo: Optional[int]
    pos: Pos
    last_dir: Optional[Dir]
    life: int
    gold: int
    timed_out: bool
    last_respawn: Optional[int] = None

    # Constants
    MAX_LIFE = 100
    BEER_LIFE = 50
    BEER_GOLD = -2
    DAY_LIFE = -1
    MINE_LIFE = -20
    DEFEND_LIFE = -20

    @classmethod
    def create(
        cls,
        id: int,
        name: str,
        user_id: Optional[str],
        elo: Optional[int],
        pos: Pos,
        token: str,
    ) -> "Hero":
        """Create a new hero with default values."""
        return cls(
            id=id,
            token=token,
            name=name,
            user_id=user_id,
            elo=elo,
            pos=pos,
            last_dir=None,
            life=cls.MAX_LIFE,
            gold=0,
            timed_out=False,
            last_respawn=None,
        )

    def move_to(self, pos: Pos) -> "Hero":
        """Move hero to new position."""
        return replace(self, pos=pos)

    def with_last_dir(self, direction: Dir) -> "Hero":
        """Set last direction."""
        return replace(self, last_dir=direction)

    def with_life(self, diff: int) -> "Hero":
        """Adjust life by diff (clamped to 0-MAX_LIFE)."""
        new_life = max(0, min(self.MAX_LIFE, self.life + diff))
        return replace(self, life=new_life)

    def with_gold(self, diff: int) -> "Hero":
        """Adjust gold by diff (min 0)."""
        new_gold = max(0, self.gold + diff)
        return replace(self, gold=new_gold)

    def can_afford_beer(self) -> bool:
        """Check if hero can afford beer."""
        return self.gold >= abs(self.BEER_GOLD)

    def drink_beer(self) -> "Hero":
        """Drink beer at tavern: -2 gold, +50 life."""
        if self.can_afford_beer():
            return self.with_gold(self.BEER_GOLD).with_life(self.BEER_LIFE)
        return self

    def defend(self) -> "Hero":
        """Defend against attack: -20 life."""
        return self.with_life(self.DEFEND_LIFE)

    def fight_mine(self) -> "Hero":
        """Attack mine: -20 life."""
        return self.with_life(self.MINE_LIFE)

    def day(self) -> "Hero":
        """Apply daily life drain: -1 life (respawn if dead)."""
        hero = self.with_life(self.DAY_LIFE)
        if hero.is_dead():
            return hero.with_life(1)
        return hero

    def respawn(self, pos: Pos, turn: int) -> "Hero":
        """Respawn at position with full life."""
        return replace(
            self,
            life=self.MAX_LIFE,
            pos=pos,
            last_respawn=turn,
        )

    def set_timed_out(self) -> "Hero":
        """Mark hero as timed out."""
        return replace(self, timed_out=True)

    def is_alive(self) -> bool:
        """Check if hero is alive."""
        return self.life > 0

    def is_dead(self) -> bool:
        """Check if hero is dead."""
        return not self.is_alive()

    def needs_respawn(self) -> bool:
        """Check if hero needs to be respawned."""
        return self.is_dead()

    @property
    def crashed(self) -> bool:
        """Check if hero crashed (timed out)."""
        return self.timed_out

    def with_name(self, name: str) -> "Hero":
        """Set hero name."""
        return replace(self, name=name)

    def with_user_id(self, user_id: Optional[str]) -> "Hero":
        """Set hero user ID."""
        return replace(self, user_id=user_id)

    def with_elo(self, elo: Optional[int]) -> "Hero":
        """Set hero ELO rating."""
        return replace(self, elo=elo)

    def render(self) -> str:
        """Render hero as string."""
        return f"@{self.id}"

    def __str__(self) -> str:
        return f"Hero[{self.id}]({self.name}): life={self.life}, gold={self.gold}, pos={self.pos}"
