# Implementation Plan: Vindinium Python Rewrite

**Branch**: `001-vindinium-python-rewrite` | **Date**: 2026-01-09 | **Spec**: [specs/001-vindinium-python-rewrite/spec.md](spec.md)
**Input**: Feature specification from `specs/001-vindinium-python-rewrite/spec.md`

## Summary

Rewrite the Vindinium game server from Scala/Play Framework to Python/FastAPI. The system will faithfully reproduce the original game mechanics (Arbiter) while leveraging modern Python features like async I/O and strict typing. Core components include an immutable game model, a pure functional game rules engine, and a MongoDB-backed persistence layer.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (Web), Motor (Async MongoDB), Pydantic (Validation), Hypothesis (Property Testing)
**Storage**: MongoDB 4.4+
**Testing**: pytest + Hypothesis (Property-based testing required by Constitution)
**Target Platform**: Unix/Linux (Dockerized)
**Project Type**: Web Application (API Server)
**Performance Goals**: < 100ms API response time; Support 100+ concurrent games
**Constraints**: Must match original Scala game logic exactly; Pure functional core (Arbiter)
**Scale/Scope**: Server-side logic for multiplayer game; ~3-4k LOC estimated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Immutability by Default**: ✅ Design explicitly mandates `frozen=True` dataclasses and state transitions returning new instances.
- **Property-Based Verification**: ✅ Testing strategy includes Hypothesis for all core mechanics (movement, combat, etc.).
- **Functional Fidelity**: ✅ Explicit goal is to reproduce Scala mechanics; migration strategy includes side-by-side comparison.
- **Explicit Typing & Layers**: ✅ Architecture defined as API -> Arbiter -> Models; Python 3.11+ typing enforced.

## Project Structure

### Documentation (this feature)

```text
specs/001-vindinium-python-rewrite/
├── plan.md              # This file
├── research.md          # Technical choices and architecture
├── data-model.md        # Entity definitions and invariants
├── quickstart.md        # Developer setup guide
├── contracts/           # API specifications
│   └── api.yaml         # OpenAPI definition
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
python/
├── vindinium/
│   ├── models/          # Immutable data structures (Hero, Board, Game)
│   ├── game_logic/      # Pure functional core (Arbiter, Generator)
│   ├── api/             # FastAPI routes and DTOs
│   ├── db/              # MongoDB repositories
│   └── system/          # ELO, Matchmaking, Replay
└── tests/
    ├── unit/            # Property tests for models/logic
    └── integration/     # API and DB tests
```

**Structure Decision**: Adopting the standard Python package structure within `python/` directory as specified in the pre-existing implementation plan, enforcing strict separation between logic (pure) and I/O (impure).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (None) | | |