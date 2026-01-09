# Copilot Agent Workflow Guide

This guide provides a step-by-step workflow for GitHub Copilot agents working on Vindinium tasks.

## 🎯 Before You Start

### Required Reading (in order)
1. `.github/copilot-instructions.md` - Full project guidelines
2. `CONTRIBUTING.md` - Quick workflow reference
3. Your GitHub issue - Task-specific requirements
4. `specs/001-vindinium-python-rewrite/tasks.md` - Task dependencies

### Key Files to Know
- `GEMINI.md` - Current project state
- `specs/001-vindinium-python-rewrite/spec.md` - Requirements
- `specs/001-vindinium-python-rewrite/data-model.md` - Entity definitions
- `specs/001-vindinium-python-rewrite/plan.md` - Architecture decisions
- `python/QUICKSTART.md` - Setup instructions

## 📋 Task Types

### Type 1: Property Test Tasks (T005-T007, T014-T017, T024-T025)

**Goal**: Write Hypothesis property tests that verify game invariants.

**Steps**:
1. Read the issue description (it includes requirement mapping)
2. Identify invariants to test (listed in issue)
3. Design Hypothesis strategies to generate test data
4. Implement property tests
5. Run and verify: `pytest python/tests/unit/test_*.py -v --hypothesis-show-statistics`

**Example Pattern**:
```python
from hypothesis import given, strategies as st
from vindinium.models.pos import Pos, Dir

@given(st.integers(), st.integers())
def test_movement_reversibility(x: int, y: int):
    """Moving North then South returns to original position."""
    original = Pos(x=x, y=y)
    moved = original.move_to(Dir.NORTH).move_to(Dir.SOUTH)
    assert moved == original, "Reversible movement failed"
```

**Checklist**:
- [ ] Read requirement from issue
- [ ] Identify all invariants
- [ ] Create Hypothesis strategy
- [ ] Write property test with clear assertion messages
- [ ] Run with `pytest -v --hypothesis-show-statistics`
- [ ] Verify it fails when invariant is broken (test the test!)

---

### Type 2: Model Implementation Tasks (T008-T012)

**Goal**: Create immutable game models (Pos, Hero, Board, Game).

**Steps**:
1. Check that related test task is complete (see tasks.md dependencies)
2. Read entity definition from `specs/001-vindinium-python-rewrite/data-model.md`
3. Implement as frozen dataclass with type hints
4. Add methods that return new instances (no mutation!)
5. Run tests: `pytest python/tests/unit/test_*.py -v`
6. Lint: `ruff check python/`

**Example Pattern**:
```python
from dataclasses import dataclass, replace
from typing import Self

@dataclass(frozen=True)
class Hero:
    """Immutable hero representation.
    
    Invariants:
    - 0 <= life <= 100
    - gold >= 0
    """
    id: int
    life: int  # 0-100
    gold: int  # >= 0
    pos: Pos
    spawn_pos: Pos
    
    def take_damage(self, amount: int) -> Self:
        """Return new hero with reduced life (min 0)."""
        return replace(self, life=max(0, self.life - amount))
    
    def add_gold(self, amount: int) -> Self:
        """Return new hero with increased gold."""
        return replace(self, gold=self.gold + amount)
    
    def respawn(self) -> Self:
        """Return new hero at spawn position with full health."""
        return replace(self, pos=self.spawn_pos, life=100)
```

**Checklist**:
- [ ] Model uses `@dataclass(frozen=True)`
- [ ] All fields have type hints
- [ ] No `__init__` or `__setattr__` (use frozen dataclass)
- [ ] Methods return `Self` (new instances)
- [ ] Use `dataclasses.replace()` for updates
- [ ] Docstrings explain invariants
- [ ] Tests pass: `pytest`
- [ ] Linting passes: `ruff check`

---

### Type 3: Game Logic Tasks (T018-T023)

**Goal**: Implement pure functional game rules in the Arbiter class.

**Steps**:
1. **CRITICAL**: Verify related property tests exist and pass
2. Read game rules from `specs/001-vindinium-python-rewrite/spec.md`
3. Implement as static methods or pure functions
4. Never mutate input - always return new Game instance
5. Run all tests: `pytest python/tests/ -v`

**Example Pattern**:
```python
class Arbiter:
    """Pure functional game rules engine."""
    
    @staticmethod
    def process_move(game: Game, hero_id: int, direction: Dir) -> Game:
        """Process hero movement and return new game state.
        
        Rules:
        - Walls block movement (hero stays in place)
        - Hero collisions block movement
        - Out of bounds blocks movement
        
        Args:
            game: Current immutable game state
            hero_id: ID of hero making the move (1-4)
            direction: Direction to move
            
        Returns:
            New Game instance with updated state
        """
        hero = game.get_hero(hero_id)
        new_pos = hero.pos.move_to(direction)
        
        # Check collisions
        if not game.board.is_valid_position(new_pos):
            return game  # Blocked by bounds or wall
        
        if game.has_hero_at(new_pos):
            return game  # Blocked by another hero
        
        # Move succeeded - return new game state
        new_hero = hero.move(new_pos)
        return game.update_hero(hero_id, new_hero)
    
    @staticmethod
    def resolve_combat(game: Game, attacker_id: int) -> Game:
        """Apply combat damage to adjacent heroes.
        
        Returns:
            New Game with updated hero states
        """
        attacker = game.get_hero(attacker_id)
        adjacent_heroes = game.get_adjacent_heroes(attacker.pos)
        
        new_heroes = list(game.heroes)
        for defender in adjacent_heroes:
            damaged = defender.take_damage(20)
            if damaged.life == 0:
                # Hero dies: respawn and transfer mines
                respawned = damaged.respawn()
                new_board = game.board.transfer_mines(defender.id, attacker_id)
                new_heroes[defender.id - 1] = respawned
            else:
                new_heroes[defender.id - 1] = damaged
        
        return replace(game, heroes=tuple(new_heroes))
```

**Checklist**:
- [ ] Property tests exist and pass
- [ ] Functions are pure (no side effects, no I/O)
- [ ] Never mutate input arguments
- [ ] Always return new Game instance
- [ ] Handle all edge cases from spec
- [ ] Add clear docstrings with rules
- [ ] Tests pass: `pytest python/tests/unit/test_arbiter*.py -v`
- [ ] Integration works: `pytest python/tests/ -v`

---

### Type 4: API/Database Tasks (T024-T032)

**Goal**: Expose game engine via FastAPI and persist to MongoDB.

**Steps**:
1. Ensure Arbiter (game logic) is complete
2. For DB tasks: Setup async Motor connection
3. For API tasks: Create FastAPI endpoints
4. Keep I/O separate from game logic
5. Run integration tests: `pytest python/tests/integration/ -v`

**MongoDB Example**:
```python
# python/vindinium/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class MongoDB:
    """Async MongoDB connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect(cls, uri: str, db_name: str):
        """Establish connection to MongoDB."""
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
```

**FastAPI Example**:
```python
# python/vindinium/api/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class TrainingRequest(BaseModel):
    turns: int = 300
    map: str = "m1"

@router.post("/api/training")
async def start_training(request: TrainingRequest):
    """Create a new training game.
    
    Returns game state JSON.
    """
    # 1. Validate input
    if request.turns < 1 or request.turns > 300:
        raise HTTPException(400, "Turns must be 1-300")
    
    # 2. Use game logic (pure functions)
    from vindinium.game_logic.map_parser import MapParser
    from vindinium.game_logic.generator import Generator
    
    board = MapParser.parse_map(get_map_string(request.map))
    game = Generator.create_initial_game_state(board, turns=request.turns)
    
    # 3. Persist to DB
    from vindinium.db.repositories import GameRepository
    game_id = await GameRepository.save(game)
    
    # 4. Return response
    return {
        "game": game.to_dict(),
        "token": generate_token(),
        "viewUrl": f"/game/{game_id}"
    }
```

**Checklist**:
- [ ] Separation of concerns: API ← Logic → DB
- [ ] Use async/await for I/O operations
- [ ] Arbiter (logic) remains pure
- [ ] Pydantic models for request/response validation
- [ ] Error handling with proper HTTP status codes
- [ ] Integration tests pass
- [ ] API matches `specs/001-vindinium-python-rewrite/contracts/api.yaml`

---

## 🔍 Common Issues & Solutions

### Issue: "Tests are failing"
**Solution**: 
1. Read the test failure message carefully
2. Check if you're mutating state instead of returning new instances
3. Verify invariants are maintained
4. Use `pytest -vv` for detailed output

### Issue: "How do I make immutable updates?"
**Solution**:
```python
from dataclasses import replace

# ✅ CORRECT: Return new instance
new_hero = replace(old_hero, life=50)

# ❌ WRONG: Mutation
old_hero.life = 50  # Will fail - frozen dataclass!
```

### Issue: "Task dependencies unclear"
**Solution**: Check `specs/001-vindinium-python-rewrite/tasks.md`:
- Phases run sequentially: Setup → Models → Logic → API
- Tasks marked `[P]` can run in parallel
- Tests MUST complete before implementation

### Issue: "Where is the requirement specification?"
**Solution**: Check your GitHub issue - it has "Requirements Mapping" section linking to spec.md

---

## ✅ Pre-Commit Checklist

Before submitting any work:

```bash
# 1. Run tests
pytest python/tests/ -v

# 2. Check lint
ruff check python/

# 3. Type check (optional but recommended)
mypy python/vindinium --strict

# 4. Verify no files were incorrectly modified
git status
git diff

# 5. Ensure constitutional principles followed
# - Models are frozen dataclasses? ✓
# - Property tests exist for mechanics? ✓
# - Arbiter functions are pure? ✓
# - Type hints everywhere? ✓
```

---

## 📚 Quick Reference Links

| Need | File |
|------|------|
| Full guidelines | `.github/copilot-instructions.md` |
| Quick start | `CONTRIBUTING.md` |
| Requirements | `specs/001-vindinium-python-rewrite/spec.md` |
| Architecture | `specs/001-vindinium-python-rewrite/plan.md` |
| Data models | `specs/001-vindinium-python-rewrite/data-model.md` |
| API contract | `specs/001-vindinium-python-rewrite/contracts/api.yaml` |
| Task list | `specs/001-vindinium-python-rewrite/tasks.md` |
| Setup guide | `python/QUICKSTART.md` |
| Current state | `GEMINI.md` |

---

## 💡 Tips for Success

1. **Read before coding** - The issue has everything you need
2. **Tests first** - Property tests are non-negotiable
3. **Small commits** - One task = one focused change
4. **Run tests often** - Catch issues early
5. **Check dependencies** - Some tasks block others
6. **Ask questions** - Better to clarify than guess

---

Happy coding! 🎮🐍
