# Research & Technical Decisions

## Technology Choices

### Web Framework: FastAPI
- **Decision**: Use FastAPI.
- **Rationale**: 
  - Native async support is critical for handling concurrent long-polling/websocket connections efficiently.
  - Automatic OpenAPI generation simplifies client integration.
  - Pydantic integration ensures strict type validation for game inputs.
- **Alternatives**: 
  - *Flask*: Rejected due to synchronous nature and lack of built-in async/type-safety features.
  - *Django*: Rejected as too heavy; ORM not needed for MongoDB.

### Database Driver: Motor
- **Decision**: Use Motor (Async MongoDB driver).
- **Rationale**: 
  - Non-blocking I/O allows the server to handle other game moves while persisting state.
  - Native support for Python's `async/await` syntax.
- **Alternatives**: 
  - *PyMongo*: Synchronous, would block the event loop.

### Testing Strategy: Hypothesis
- **Decision**: Use Hypothesis for Property-Based Testing.
- **Rationale**: 
  - **Constitution Requirement**: The Constitution explicitly mandates property-based verification.
  - **Game Logic**: Complex state transitions (movement, combat) are better verified by defining invariants (e.g., "Health never < 0") than examples.
- **Alternatives**: 
  - *Example-based only (pytest)*: Insufficient for guaranteeing correctness of the game engine against edge cases.

## Architectural Patterns

### Functional Core, Imperative Shell
- **Decision**: Isolate game logic (`Arbiter`) as pure functions operating on immutable models.
- **Rationale**:
  - **Testability**: Pure functions are trivial to test (no mocks needed).
  - **Replayability**: Immutable state makes implementing "time travel" or replays trivial (just store state snapshots).
  - **Concurrency**: Immutable data structures are thread-safe by default.

### Hexagonal Architecture (Ports & Adapters)
- **Decision**: Keep domain logic independent of Framework/DB.
- **Rationale**: Allows testing game rules without spinning up a web server or database.

## Unknowns & Clarifications

### Map Parsing Format
- **Status**: Resolved.
- **Details**: 
  - `##`: Wall
  - `  `: Air
  - `[]`: Tavern
  - `$-`: Neutral Mine
  - `$1`-`$4`: Owned Mine
  - Format is a string row-by-row.

### ELO System
- **Status**: Resolved.
- **Details**: Standard ELO implementation. K-factor to be determined (start with 32).
