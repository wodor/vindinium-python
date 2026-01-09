# Contributing to Vindinium Python Rewrite

## For GitHub Copilot Agents

Welcome! This project follows strict architectural principles. Please read carefully before starting work.

### Quick Start

1. **Read First**: `.github/copilot-instructions.md` (comprehensive guide)
2. **Check State**: `GEMINI.md` (current technologies and changes)
3. **Find Your Task**: Look at your GitHub issue - it has detailed context
4. **Review Specs**: `/specs/001-vindinium-python-rewrite/` directory

### Constitutional Rules (Non-Negotiable)

🔒 **Immutability**: All models use `frozen=True` dataclasses  
🔒 **Tests First**: Property-based tests BEFORE implementation  
🔒 **Pure Functions**: Game logic (Arbiter) has NO side effects  
🔒 **Type Safety**: Strict type hints everywhere  

### Workflow

```bash
# 1. Understand the task
cat specs/001-vindinium-python-rewrite/tasks.md | grep "T0XX"

# 2. Read requirements
cat specs/001-vindinium-python-rewrite/spec.md

# 3. For test tasks: Write Hypothesis property tests
# 4. For implementation: Make sure tests exist first

# 5. Run tests
pytest python/tests/unit/test_*.py -v

# 6. Lint code
ruff check python/

# 7. Verify everything passes
pytest python/tests/ -v && ruff check python/
```

### Task Dependencies

Check `specs/001-vindinium-python-rewrite/tasks.md` for dependencies:
- Phase 1 (Setup) → Phase 2 (Models) → Phase 3 (Mechanics) → Phase 4 (API)
- Tasks marked `[P]` can run in parallel
- Test tasks must complete BEFORE their implementation tasks

### Common Patterns

**Immutable Update**:
```python
@dataclass(frozen=True)
class Hero:
    life: int
    gold: int
    
    def take_damage(self, amount: int) -> Self:
        return dataclasses.replace(self, life=max(0, self.life - amount))
```

**Property Test**:
```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=100))
def test_health_bounds(initial_health: int):
    hero = Hero(life=initial_health, gold=0)
    damaged = hero.take_damage(20)
    assert 0 <= damaged.life <= 100
```

**Pure Function**:
```python
class Arbiter:
    @staticmethod
    def process_move(game: Game, hero_id: int, direction: Dir) -> Game:
        """Returns NEW game state - never mutates input."""
        # ... logic ...
        return new_game  # Always return new instance
```

### File Locations

- Models: `python/vindinium/models/`
- Game Logic: `python/vindinium/game_logic/`
- API: `python/vindinium/api/`
- Unit Tests: `python/tests/unit/`
- Integration Tests: `python/tests/integration/`

### Before Submitting

- [ ] All tests pass: `pytest python/tests/ -v`
- [ ] Linting passes: `ruff check python/`
- [ ] Type checking passes: `mypy python/vindinium --strict`
- [ ] Code follows immutability principles
- [ ] Property tests exist for new game mechanics

### Questions?

1. Architecture → `specs/001-vindinium-python-rewrite/plan.md`
2. Requirements → `specs/001-vindinium-python-rewrite/spec.md`
3. Data Models → `specs/001-vindinium-python-rewrite/data-model.md`
4. API Contracts → `specs/001-vindinium-python-rewrite/contracts/api.yaml`

---

## For Human Contributors

If you're a human developer:

1. Set up your environment: See `specs/001-vindinium-python-rewrite/quickstart.md`
2. Pick an open issue from GitHub
3. Follow the same constitutional rules above
4. Create a feature branch: `git checkout -b feature/T0XX-description`
5. Submit a PR with passing tests

Thank you for contributing! 🎮
