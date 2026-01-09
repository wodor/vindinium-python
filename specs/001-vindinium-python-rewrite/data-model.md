# Data Model

## Core Entities (Immutable)

### Position (Pos)
Represents a coordinate on the game board.
- **Fields**:
  - `x`: int (Row index, 0-based)
  - `y`: int (Column index, 0-based)
- **Invariants**:
  - `x` and `y` must be within board bounds [0, size-1].
- **Methods**:
  - `move(dir: Dir) -> Pos`: Returns new Pos.
  - `neighbors() -> List[Pos]`: Returns adjacent positions.

### Hero
Represents a player in the game.
- **Fields**:
  - `id`: int (1-4)
  - `name`: str
  - `pos`: Pos
  - `life`: int (0-100)
  - `gold`: int (>= 0)
  - `crashed`: bool (True if timed out/error)
  - `mineCount`: int (Computed or stored)
  - `spawnPos`: Pos
- **Invariants**:
  - `life` is always within [0, 100].
  - `gold` is never negative.
- **Transitions**:
  - `drink_beer()`: life +50 (max 100), gold -2.
  - `fight()`: life -20.
  - `die()`: life = 100, pos = spawnPos.

### Board
Represents the game map.
- **Fields**:
  - `size`: int (e.g., 20 for 20x20)
  - `tiles`: List[Tile] (Flat list or 2D array representation)
- **Methods**:
  - `at(pos: Pos) -> Tile`
  - `update(pos: Pos, tile: Tile) -> Board`: Returns new Board.

### Game
Represents the full state of a match.
- **Fields**:
  - `id`: str (Unique ID)
  - `turn`: int (Current turn number)
  - `maxTurns`: int (Total turns)
  - `status`: GameStatus (CREATED, STARTED, FINISHED)
  - `board`: Board
  - `heroes`: List[Hero] (Fixed size 4)
- **Methods**:
  - `finished`: bool (Derived from status/turn)

## Enums

### Tile
- `AIR`: Empty space
- `WALL`: Impassable
- `TAVERN`: Beer source
- `MINE(owner: Optional[int])`: Gold source

### Direction (Dir)
- `NORTH`, `SOUTH`, `EAST`, `WEST`, `STAY`

### GameStatus
- `CREATED`: Waiting for players
- `STARTED`: In progress
- `ALL_CRASHED`: Aborted
- `TURN_MAX`: Completed normally
