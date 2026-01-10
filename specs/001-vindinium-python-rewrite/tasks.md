---
description: "Task list for Vindinium Python Rewrite"
---

# Tasks: Vindinium Python Rewrite

**Input**: Design documents from `specs/001-vindinium-python-rewrite/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: **MANDATORY**. Per Project Constitution, every game mechanic logic MUST be preceded by a property-based test (Hypothesis).

**Organization**: Tasks are grouped by User Story / Logical Phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel
- **[Story]**: [US1] Core/State, [US2] Mechanics, [US3] API

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure `python/vindinium/{models,game_logic,api,db,system}`
- [x] T002 Initialize `python/requirements.txt` (FastAPI, Motor, Pydantic, Hypothesis) and `python/pyproject.toml`
- [x] T003 [P] Configure `python/.env` and `python/config.py` using `python-dotenv`
- [x] T004 [P] Setup `python/pytest.ini` and test directory structure

## Phase 2: User Story 1 - Core Engine & State (Priority: P1)

**Goal**: Implement immutable models and map parsing to represent the game state.
**Independent Test**: Can parse a map string into a Game object and verify structural invariants.

### Tests for US1 (Property-Based)

- [x] T005 [P] [US1] Create property test for Position navigation/bounds in `python/tests/unit/test_models.py`
- [x] T006 [P] [US1] Create property test for Map Parsing round-trip in `python/tests/unit/test_map_parser.py`
- [x] T007 [P] [US1] Create property test for Game initialization invariants in `python/tests/unit/test_game_state.py`

### Implementation for US1

- [x] T008 [P] [US1] Implement immutable `Pos` and `Dir` models in `python/vindinium/models/pos.py`
- [x] T009 [P] [US1] Implement `Tile` enum in `python/vindinium/models/tile.py`
- [x] T010 [P] [US1] Implement immutable `Hero` model in `python/vindinium/models/hero.py`
- [x] T011 [P] [US1] Implement immutable `Board` model in `python/vindinium/models/board.py`
- [x] T012 [P] [US1] Implement immutable `Game` model in `python/vindinium/models/game.py`
- [x] T013 [US1] Implement `MapParser` and `Generator` in `python/vindinium/game_logic/map_parser.py` (depends on Board/Tile)

## Phase 3: User Story 2 - Game Mechanics (Arbiter) (Priority: P1)

**Goal**: Implement the pure functional rules engine (Arbiter) handling moves, combat, and economy.
**Independent Test**: Simulate a sequence of moves and verify game state transitions match expectations (and invariants).

### Tests for US2 (Property-Based) ⚠️ CRITICAL

- [x] T014 [P] [US2] Property test: Movement invariants (walls, bounds) in `python/tests/unit/test_arbiter_properties.py`
- [x] T015 [P] [US2] Property test: Combat invariants (damage, respawn) in `python/tests/unit/test_arbiter_combat.py`
- [x] T016 [P] [US2] Property test: Economy invariants (mining, income) in `python/tests/unit/test_arbiter_economy.py`
- [x] T017 [P] [US2] Property test: Tavern invariants (healing limits, gold cost) in `python/tests/unit/test_arbiter_tavern.py`

### Implementation for US2

- [x] T018 [US2] Scaffold `Arbiter` class in `python/vindinium/game_logic/arbiter.py`
- [x] T019 [US2] Implement `Arbiter.process_move` (movement & collision) in `python/vindinium/game_logic/arbiter.py`
- [x] T020 [US2] Implement `Arbiter.resolve_combat` in `python/vindinium/game_logic/arbiter.py`
- [x] T021 [US2] Implement `Arbiter.handle_mines_and_economy` in `python/vindinium/game_logic/arbiter.py`
- [x] T022 [US2] Implement `Arbiter.handle_tavern` in `python/vindinium/game_logic/arbiter.py`
- [x] T023 [US2] Implement `Arbiter.finalize_turn` (death, respawn, cleanup) in `python/vindinium/game_logic/arbiter.py`

## Phase 4: User Story 3 - API & Persistence (Priority: P2)

**Goal**: Expose the game engine via FastAPI and persist state to MongoDB.
**Independent Test**: Spin up API, start game, make moves, verify JSON response.

### Tests for US3

- [ ] T024 [P] [US3] Contract test for `/api/training` in `python/tests/integration/test_api_training.py`
- [ ] T025 [P] [US3] Contract test for `/api/{gameId}/{token}/{dir}` in `python/tests/integration/test_api_move.py`

### Implementation for US3

- [x] T026 [P] [US3] Setup MongoDB connection in `python/vindinium/db/mongodb.py`
- [x] T027 [P] [US3] Implement GameRepository in `python/vindinium/db/repositories.py`
- [x] T028 [US3] Create FastAPI app entry point in `python/main.py`
- [x] T029 [US3] Implement `POST /api/training` endpoint in `python/vindinium/api/routes.py`
- [x] T030 [US3] Implement `POST /api/{gameId}/{token}/{dir}` endpoint in `python/vindinium/api/routes.py`
- [x] T031 [US3] Implement `GET /api/game/{gameId}` endpoint in `python/vindinium/api/routes.py`
- [x] T032 [US3] Add Error Handling & Logging middleware in `python/vindinium/api/middleware.py`

## Phase 5: Polish & Integration

- [ ] T033 Verify all Hypothesis tests pass with high example count
- [ ] T034 Run full game simulation integration test
- [ ] T035 Update `python/README.md` with usage instructions
- [ ] T036 Dockerize application (Dockerfile & docker-compose.yml)

## Dependencies

- **Setup**: Blocking
- **US1 (Core)**: Blocks US2 and US3
- **US2 (Arbiter)**: Blocks US3 (API needs engine to work)
- **US3 (API)**: Final user-facing layer

## Parallel Execution

- **Models**: T008-T012 can be built in parallel.
- **Tests**: All property tests (T014-T017) can be written in parallel before logic.
- **API**: Endpoints (T029-T031) can be scaffolded in parallel.