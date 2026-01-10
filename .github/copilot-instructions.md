# GitHub Copilot Agent Instructions

## Project Overview

**Vindinium Python Rewrite** - Multiplayer AI programming challenge game server being rewritten from Scala/Play Framework to Python 3.11+ with FastAPI.

### Key Information
- **Main Implementation**: `/python/` directory
- **Feature Specs**: `/specs/001-vindinium-python-rewrite/`
- **Project Constitution**: Immutability-first, property-based testing, functional core
- **Current State**: Check `/GEMINI.md` for active technologies and recent changes

## Core Architecture

### Technology Stack
- **Web Framework**: FastAPI
- **Database**: MongoDB (Motor for async operations)
- **Validation**: Pydantic v2
- **Testing**: pytest + Hypothesis (property-based testing)
- **Python Version**: 3.11+

### Project Structure
```
python/
├── vindinium/
│   ├── models/          # Immutable game entities (Pos, Hero, Board, Game)
│   ├── game_logic/      # Pure functional rules engine (Arbiter, MapParser)
│   ├── api/             # FastAPI routes and middleware
│   ├── db/              # MongoDB repositories
│   └── system/          # Configuration and utilities
└── tests/
    ├── unit/            # Property-based tests with Hypothesis
    └── integration/     # API contract tests
```

## Constitutional Principles (MANDATORY)

### 1. Immutability by Default
- **ALL game models MUST use `frozen=True`** dataclasses
- State transitions return NEW instances (never mutate)
- Example: `hero.take_damage(20)` returns a new Hero object

### 2. Property-Based Testing Required
- **Every game mechanic MUST be preceded by a Hypothesis test**
- Write tests BEFORE implementation
- Verify invariants, not just happy paths
- Example: Test that `position.move(North).move(South) == position`

### 3. Functional Core, Imperative Shell
- **Arbiter** (game logic) MUST be pure functions (no I/O, no side effects)
- API layer handles I/O (database, HTTP)
- Keep business logic separate from infrastructure

### 4. Explicit Typing
- Use Python 3.11+ type hints everywhere
- Leverage Pydantic for validation
- No `Any` types in core logic

## Development Workflow

### Before Starting Any Task

1. **Read the task specification** in `/specs/001-vindinium-python-rewrite/tasks.md`
2. **Check dependencies** - Some tasks block others (see tasks.md Phase structure)
3. **Review related specs**:
   - `spec.md` - Requirements and acceptance criteria
   - `data-model.md` - Entity definitions and invariants
   - `plan.md` - Architecture decisions
4. **Read related issue description** on GitHub (has detailed context)

### Task Execution Pattern

For **Test Tasks** (T005-T007, T014-T017, T024-T025):
1. Review the requirement mapping in the issue
2. Identify the invariants to verify
3. Write Hypothesis strategy to generate test data
4. Implement property test asserting invariants
5. Run test with `pytest python/tests/unit/test_*.py -v`

For **Implementation Tasks** (T008-T013, T018-T023, T026-T032):
1. **Tests MUST exist first** (check tasks.md for which test task blocks this)
2. Implement using immutable patterns
3. Follow type hints from `data-model.md`
4. Run tests: `pytest python/tests/ -v`
5. Run linter: `ruff check python/`

### Testing Commands

```bash
# Run specific test file
pytest python/tests/unit/test_models.py -v

# Run with Hypothesis verbose output
pytest python/tests/unit/test_arbiter_properties.py -v --hypothesis-show-statistics

# Run all tests
pytest python/tests/ -v

# Lint code
ruff check python/
```

### Validation Before PR

```bash
# Must pass all three:
pytest python/tests/ -v
ruff check python/
python -m mypy python/vindinium --strict
```

## Key Requirements Reference

### Game Mechanics (from spec.md)

1. **Movement**: North(-x), South(+x), East(+y), West(-y), Stay
2. **Walls**: Block movement (hero stays in place)
3. **Combat**: Adjacent heroes fight automatically (defender -20 HP)
4. **Mines**: Capture costs 20 HP, earns 1 gold/turn
5. **Taverns**: Cost 2 gold, restore 50 HP (max 100)
6. **Death**: Hero respawns at spawn position with 100 HP, loses all mines

### Invariants to Maintain (CRITICAL)

From `/specs/001-vindinium-python-rewrite/data-model.md`:

- Hero health: 0 ≤ life ≤ 100
- Hero gold: gold ≥ 0
- Position bounds: 0 ≤ x, y < board.size
- Board size: MUST be even number
- Exactly 4 heroes per game
- Turn order: Hero 1 → 2 → 3 → 4 → 1...

## Common Patterns

### Immutable Model Example
```python
from dataclasses import dataclass
from typing import Self

@dataclass(frozen=True)
class Hero:
    id: int
    life: int
    gold: int
    pos: Pos
    
    def take_damage(self, amount: int) -> Self:
        """Returns new Hero with reduced life."""
        return Hero(
            id=self.id,
            life=max(0, self.life - amount),
            gold=self.gold,
            pos=self.pos
        )
```

### Property Test Example
```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_position_navigation_reversibility(x: int, y: int):
    """Moving North then South returns to original position."""
    pos = Pos(x=x, y=y)
    moved = pos.move_to(Dir.NORTH).move_to(Dir.SOUTH)
    assert moved == pos
```

### Arbiter Pattern Example
```python
class Arbiter:
    @staticmethod
    def process_move(game: Game, hero_id: int, direction: Dir) -> Game:
        """Pure function: returns new Game after processing move."""
        hero = game.heroes[hero_id - 1]
        new_pos = hero.pos.move_to(direction)
        
        # Check collisions (walls, bounds, other heroes)
        if not game.board.is_valid_position(new_pos):
            return game  # No change
            
        # Return new game state
        new_hero = hero.move(new_pos)
        return game.update_hero(hero_id, new_hero)
```

## Task-Specific Guidance

### Phase 2: Core Engine (US1)
- Focus: Immutable models, map parsing
- Dependencies: None (can start immediately)
- Parallel: T008-T012 can be done simultaneously

### Phase 3: Game Mechanics (US2)
- Focus: Arbiter implementation
- **CRITICAL**: Tests (T014-T017) MUST pass before implementation
- Dependencies: Requires Phase 2 models
- Parallel: Individual mechanic tests can be written in parallel

### Phase 4: API & Persistence (US3)
- Focus: FastAPI routes, MongoDB integration
- Dependencies: Requires working Arbiter from Phase 3
- Parallel: T026-T027 (DB) independent from T024-T025 (tests)

## Issue Labels

When working on tasks, look for these labels:
- `phase-2-core` - Core models and state
- `phase-3-mechanics` - Game rules (Arbiter)
- `phase-4-api` - Web API and persistence
- `property-test` - Requires Hypothesis testing
- `us1`, `us2`, `us3` - User story grouping
- `parallel-safe` - Can be done alongside other [P] tasks

## Getting Help

1. **Architecture questions**: See `/specs/001-vindinium-python-rewrite/plan.md`
2. **Requirements unclear**: See `/specs/001-vindinium-python-rewrite/spec.md`
3. **Data model questions**: See `/specs/001-vindinium-python-rewrite/data-model.md`
4. **Setup issues**: See `/specs/001-vindinium-python-rewrite/quickstart.md`

## Custom Agents

This repository includes specialized custom agents for specific tasks:

### Available Agents
- **speckit-specify**: Create or update feature specifications
- **speckit-plan**: Execute implementation planning workflow
- **speckit-tasks**: Generate actionable, dependency-ordered tasks
- **speckit-implement**: Execute implementation plan from tasks.md
- **speckit-clarify**: Identify underspecified areas and ask clarification questions
- **speckit-analyze**: Cross-artifact consistency and quality analysis
- **speckit-constitution**: Create or update project constitution
- **speckit-taskstoissues**: Convert tasks to GitHub issues
- **speckit-checklist**: Generate custom checklists for features

### When to Use Custom Agents
- Delegate to custom agents when their expertise matches your task
- Custom agents have specialized knowledge and are more reliable for their domain
- Review their output but trust their specialized implementation
- See `.github/agents/` directory for agent definitions

## Security Guidelines

**CRITICAL - Always Follow These Rules:**

- ❌ **NEVER commit secrets, API keys, or credentials** to the repository
- ✅ Use environment variables for sensitive configuration
- ✅ Use `.env` files (and add to `.gitignore`) for local secrets
- ✅ Review all code changes for potential security vulnerabilities
- ✅ Validate all user input in API endpoints
- ✅ Use parameterized queries to prevent injection attacks
- ✅ Follow OWASP security guidelines for web applications
- ✅ Run security scanning tools before finalizing changes

### MongoDB Security
- Use connection strings from environment variables
- Never hardcode database credentials
- Use MongoDB authentication in production

### API Security
- Validate all request bodies with Pydantic
- Implement rate limiting for public endpoints
- Use HTTPS in production
- Sanitize error messages (don't leak internal details)

## Environment Setup

### Required Tools
```bash
# Python 3.11 or higher
python --version  # Should be 3.11+

# Install development dependencies
cd python
pip install -e ".[dev]"

# Verify installations
pytest --version
ruff --version
mypy --version
```

### Running the Full Validation Suite
```bash
# From repository root
cd python

# 1. Run all tests with coverage
pytest tests/ -v --cov=vindinium --cov-report=term-missing

# 2. Run linter
ruff check .

# 3. Run type checker
mypy vindinium --strict

# 4. Run all three together (pre-commit check)
pytest tests/ -v && ruff check . && mypy vindinium --strict
```

### Local Development
```bash
# Run FastAPI development server (when implemented)
uvicorn vindinium.main:app --reload --port 8000

# Run MongoDB locally (for integration tests)
docker run -d -p 27017:27017 --name vindinium-mongo mongo:latest

# Set environment variables
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DB="vindinium_dev"
```

## Troubleshooting

### Common Issues

**Issue**: Tests fail with `ModuleNotFoundError`
**Solution**: Install the package in development mode: `pip install -e ".[dev]"`

**Issue**: Type checking fails with mypy
**Solution**: Ensure all functions have type hints, including return types

**Issue**: Hypothesis tests are flaky
**Solution**: Check for hidden state mutation. All models must be frozen dataclasses.

**Issue**: Can't import from vindinium package
**Solution**: Make sure you're in the `/python` directory when running commands

**Issue**: MongoDB connection errors in tests
**Solution**: Integration tests may require a running MongoDB instance. Unit tests should not.

### Getting Help

If stuck:
1. Check the relevant spec file in `/specs/001-vindinium-python-rewrite/`
2. Review similar existing code for patterns
3. Look at the `COPILOT_WORKFLOW.md` for step-by-step guidance
4. Check if a custom agent can help with your specific task

## Repository Structure Note

⚠️ **This repository contains both legacy Scala code and new Python implementation:**

- **Legacy (Scala/Play Framework)**: Root directory, `app/`, `conf/`, `build.sbt`
  - DO NOT modify unless explicitly instructed
  - This is the original server implementation (maintenance mode)

- **Active (Python 3.11+)**: `python/` directory
  - ALL new development happens here
  - This is the rewrite in progress

When working on tasks, **always work in the `python/` directory** unless the issue specifically mentions the Scala codebase.

## Remember

- ✅ Tests before implementation
- ✅ Immutable data structures
- ✅ Pure functions in Arbiter
- ✅ Type hints everywhere
- ✅ Verify invariants with Hypothesis
- ✅ Never commit secrets or credentials
- ✅ Work in `python/` directory for all new code
- ❌ No mutation of game state
- ❌ No I/O in game logic
- ❌ No skipping property tests
- ❌ No modifying Scala code without permission
