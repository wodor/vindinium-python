---
applies_to:
  - "python/**"
---

# Python Implementation Instructions

**You are working in the Python 3.11+ rewrite of Vindinium.**

## Key Constraints

### 1. Immutability is Mandatory
- ALL models MUST use `@dataclass(frozen=True)`
- State changes return NEW instances using `dataclasses.replace()`
- No `__setattr__`, no mutation, no `self.field = value`

### 2. Property-Based Testing Required
- Every mechanic MUST have Hypothesis property tests
- Tests MUST be written BEFORE implementation
- Test invariants, not just happy paths

### 3. Pure Functional Core
- `vindinium.game_logic.arbiter` MUST be pure functions
- No I/O, no side effects, no global state
- Deterministic: same input → same output

### 4. Type Safety
- Python 3.11+ type hints on ALL functions and methods
- No `Any` types in core logic
- Leverage Pydantic v2 for validation

## Code Style

### Dataclass Pattern
```python
from dataclasses import dataclass, replace
from typing import Self

@dataclass(frozen=True)
class Hero:
    """Immutable hero entity.
    
    Invariants:
    - 0 <= life <= 100
    - gold >= 0
    """
    id: int
    life: int
    gold: int
    pos: Pos
    
    def take_damage(self, amount: int) -> Self:
        """Return new hero with reduced life."""
        return replace(self, life=max(0, self.life - amount))
```

### Testing Pattern
```python
from hypothesis import given, strategies as st

@given(
    st.integers(min_value=1, max_value=4),
    st.integers(min_value=0, max_value=100)
)
def test_hero_damage_never_negative(hero_id: int, damage: int):
    """Hero life never goes below 0."""
    hero = Hero(id=hero_id, life=50, gold=0, pos=Pos(0, 0))
    damaged = hero.take_damage(damage)
    assert damaged.life >= 0
```

### API Pattern (FastAPI)
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class GameRequest(BaseModel):
    turns: int = Field(ge=1, le=300)
    map: str = Field(pattern=r"^m\d+$")

@router.post("/api/games")
async def create_game(request: GameRequest):
    """Create new game - delegates to pure game logic."""
    # 1. Validate (Pydantic does this)
    # 2. Call pure functions
    board = MapParser.parse_map(request.map)
    game = GameGenerator.create(board, turns=request.turns)
    # 3. Persist with async I/O
    game_id = await GameRepo.save(game)
    # 4. Return response
    return {"gameId": game_id, "state": game.to_dict()}
```

## Testing Commands

```bash
# Unit tests only
pytest python/tests/unit/ -v

# Specific test file
pytest python/tests/unit/test_models.py -v

# With Hypothesis statistics
pytest python/tests/unit/test_arbiter_properties.py -v --hypothesis-show-statistics

# Integration tests (requires MongoDB)
pytest python/tests/integration/ -v

# All tests
pytest python/tests/ -v

# With coverage
pytest python/tests/ -v --cov=vindinium --cov-report=term-missing
```

## Validation Commands

```bash
# Linting
ruff check python/

# Auto-fix linting issues
ruff check python/ --fix

# Type checking
mypy python/vindinium --strict

# Full validation
pytest python/tests/ -v && ruff check python/ && mypy python/vindinium --strict
```

## Directory Structure

```
python/
├── vindinium/
│   ├── models/          # Immutable entities (Pos, Hero, Board, Game)
│   ├── game_logic/      # Pure functions (Arbiter, MapParser)
│   ├── api/             # FastAPI routes and middleware
│   ├── db/              # MongoDB repositories (async I/O)
│   └── system/          # Configuration and utilities
└── tests/
    ├── unit/            # Property-based tests (no I/O)
    └── integration/     # API and database tests
```

## What NOT To Do

❌ Modify Scala code in root directory  
❌ Mutate frozen dataclasses  
❌ Add I/O to game logic (Arbiter)  
❌ Skip property tests  
❌ Use `Any` type hints in models  
❌ Commit secrets or credentials  
❌ Break existing tests  

## What TO Do

✅ Write Hypothesis tests first  
✅ Use frozen dataclasses for models  
✅ Keep Arbiter pure (no side effects)  
✅ Add comprehensive type hints  
✅ Follow existing patterns in codebase  
✅ Run validation before committing  
✅ Work only in `python/` directory  

## Quick Reference

- **Specs**: `/specs/001-vindinium-python-rewrite/spec.md`
- **Data Models**: `/specs/001-vindinium-python-rewrite/data-model.md`
- **Architecture**: `/specs/001-vindinium-python-rewrite/plan.md`
- **Tasks**: `/specs/001-vindinium-python-rewrite/tasks.md`
- **Setup**: `/python/QUICKSTART.md`
