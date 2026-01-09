# Vindinium Python Rewrite - Implementation Plan

## Overview
Rewrite Vindinium game server from Scala/Play Framework to Python. Estimated effort: **2-4 weeks** for a single developer.

## Technology Stack

### Core Framework
- **FastAPI**: Modern async web framework (replaces Play Framework)
- **Motor**: Async MongoDB driver (replaces ReactiveMongo)
- **Pydantic**: Data validation and models
- **uvicorn**: ASGI server

### Additional Libraries
- **python-dotenv**: Configuration management
- **pytest**: Testing framework
- **httpx**: HTTP client for testing

## Project Structure
```
python/
├── vindinium/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pos.py           # Position, Direction
│   │   ├── tile.py          # Tile types (Air, Wall, Tavern, Mine)
│   │   ├── board.py         # Game board
│   │   ├── hero.py          # Hero state
│   │   ├── game.py          # Game state
│   │   └── status.py        # Game status
│   ├── game_logic/
│   │   ├── __init__.py
│   │   ├── arbiter.py       # Game rules & turn processing
│   │   ├── traverser.py     # Pathfinding algorithms
│   │   ├── generator.py     # Game/board generation
│   │   └── map_parser.py    # Parse map strings
│   ├── system/
│   │   ├── __init__.py
│   │   ├── elo.py           # ELO rating system
│   │   ├── replay.py        # Game replay storage
│   │   ├── round.py         # Arena round management
│   │   └── now_playing.py   # Active games tracking
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API endpoints
│   │   ├── training.py      # Training mode endpoints
│   │   ├── arena.py         # Arena mode endpoints
│   │   └── game.py          # Game viewing endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   ├── mongodb.py       # Database connection
│   │   └── repositories.py  # Data access layer
│   └── config.py            # Configuration
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_arbiter.py
│   └── test_api.py
├── requirements.txt
├── pyproject.toml
├── main.py                  # Application entry point
└── README.md
```

## Implementation Phases

### Phase 1: Core Models (Days 1-3)
**Goal**: Implement fundamental data structures

#### Tasks:
- [ ] `models/pos.py`: Position class with navigation methods (north, south, east, west)
- [ ] `models/tile.py`: Tile enum (Air, Wall, Tavern, Mine)
- [ ] `models/status.py`: Game status enum (Created, Started, AllCrashed, TurnMax)
- [ ] `models/hero.py`: Hero state with health, gold, position
  - Constants: maxLife=100, beerLife=50, beerGold=-2, dayLife=-1, mineLife=-20
  - Methods: drinkBeer(), fightMine(), defend(), reSpawn(), withLife(), withGold()
- [ ] `models/board.py`: Board with tile grid, size calculation
  - Methods: get(), update(), transferMine(), countMines(), mirrorX/Y()
- [ ] `models/game.py`: Game state aggregating board + 4 heroes
  - Methods: step(), setTimedOut(), withHero(), spawnPosOf()

**Validation**: Unit tests for position navigation, hero state transitions, board operations

---

### Phase 2: Game Logic (Days 4-7)
**Goal**: Implement core game mechanics

#### Tasks:
- [ ] `game_logic/map_parser.py`: Parse string maps to Board objects
  - Parse 2-char tiles: "  "=Air, "##"=Wall, "[]"=Tavern, "$-"=Mine
- [ ] `game_logic/generator.py`: Generate random maps and initial game states
- [ ] `game_logic/arbiter.py`: Core game rules engine
  - Process hero moves (North/South/East/West/Stay)
  - Handle collisions (heroes bumping into walls/each other)
  - Process tavern interactions (drink beer: -2 gold, +50 life)
  - Process mine capture (attack: -20 life, gain ownership)
  - Handle hero death & respawn
  - Gold income per turn (1 gold per owned mine)
  - Turn advancement logic
- [ ] `game_logic/traverser.py`: Pathfinding (Dijkstra/A* for bot navigation)

**Validation**: Test game scenarios (hero movement, combat, mine capture, tavern use)

---

### Phase 3: Database Layer (Days 8-10)
**Goal**: MongoDB integration for persistence

#### Tasks:
- [ ] `db/mongodb.py`: Connection management with Motor
- [ ] `db/repositories.py`: Data access patterns
  - UserRepository: findByKey(), findById(), create(), updateElo()
  - GameRepository: create(), update(), findById(), findActive()
  - ReplayRepository: save(), load()
- [ ] User model with API key authentication
- [ ] Game persistence (save state after each turn)
- [ ] Replay storage (full game history)

**Validation**: Test CRUD operations, verify data consistency

---

### Phase 4: API Endpoints (Days 11-14)
**Goal**: RESTful API with FastAPI

#### Core Endpoints:
- [ ] `POST /api/training`: Start training game
  - Parameters: key (API key), turns (optional), map (optional)
  - Returns: Game state + player token
- [ ] `POST /api/arena`: Join arena queue
  - Parameters: key (API key)
  - Returns: Game state when matched
- [ ] `POST /api/{gameId}/{dir}`: Make move
  - Parameters: gameId, direction (North/South/East/West/Stay)
  - Returns: Updated game state
- [ ] `GET /api/game/{gameId}`: View game state
- [ ] `GET /`: Landing page (serve static HTML)
- [ ] `GET /game/{gameId}`: Game viewer page

**Additional Features**:
- [ ] User registration & API key generation
- [ ] ELO rating updates after arena games
- [ ] Game timeout handling (10s per move)
- [ ] Streaming game updates (WebSocket/SSE)

**Validation**: API integration tests, load testing

---

### Phase 5: System Components (Days 15-17)
**Goal**: Arena matching, ELO, replays

#### Tasks:
- [ ] `system/elo.py`: ELO rating calculation
  - K-factor for rating adjustments
  - Win probability calculation
- [ ] `system/round.py`: Arena round management
  - Match 4 players from queue
  - Track active rounds
  - Handle player disconnections
- [ ] `system/replay.py`: Full game replay storage
  - Store every turn state
  - Replay viewer functionality
- [ ] `system/now_playing.py`: Track active games
  - Real-time game list
  - Game status monitoring

**Validation**: Test matchmaking, ELO calculations, replay playback

---

### Phase 6: Client Integration (Days 18-19)
**Goal**: Serve existing JavaScript client

#### Tasks:
- [ ] Configure static file serving for `/client` directory
- [ ] Ensure JSON format matches client expectations
- [ ] WebSocket support for live game updates
- [ ] Verify game visualization works correctly

**Validation**: Manual testing with web client, check all UI features

---

### Phase 7: Testing & Refinement (Days 20-21)
**Goal**: Comprehensive testing & bug fixes

#### Tasks:
- [ ] Unit tests for all models (>80% coverage)
- [ ] Integration tests for game logic
- [ ] API endpoint tests
- [ ] Load testing (concurrent games)
- [ ] Game logic verification against Scala version
  - Compare sample game outputs
  - Verify edge cases (crashes, respawns, timeouts)
- [ ] Performance optimization
- [ ] Documentation updates

---

### Phase 8: Deployment (Days 22-23)
**Goal**: Production-ready deployment

#### Tasks:
- [ ] Docker containerization
- [ ] Environment configuration (MongoDB URI, secrets)
- [ ] Nginx reverse proxy setup
- [ ] Logging & monitoring setup
- [ ] Migration script from Scala database (if needed)
- [ ] Deployment guide

---

## Key Implementation Notes

### Critical Game Constants
```python
# Hero constants
MAX_LIFE = 100
BEER_LIFE = 50
BEER_GOLD = -2
DAY_LIFE = -1  # Life lost per turn
MINE_LIFE = -20  # Life lost attacking mine
DEFEND_LIFE = -20  # Life lost defending mine
```

### Game Flow
1. **Initialization**: Create 4 heroes, place on spawn points
2. **Turn Loop**: 
   - Current hero receives move request (10s timeout)
   - Arbiter processes move (collision detection, state updates)
   - Apply consequences (mine income, life drain, respawns)
   - Advance to next hero
   - Check end conditions (maxTurns or all crashed)
3. **Finish**: Calculate final scores (gold), update ELO

### API Response Format
```json
{
  "game": {
    "id": "game_id",
    "turn": 42,
    "maxTurns": 300,
    "heroes": [...],
    "board": {
      "size": 18,
      "tiles": "##  []$-..."
    },
    "finished": false
  },
  "hero": {
    "id": 1,
    "name": "BotName",
    "pos": {"x": 5, "y": 7},
    "life": 80,
    "gold": 15
  },
  "token": "abc123",
  "viewUrl": "http://localhost:9000/game_id",
  "playUrl": "http://localhost:9000/api/game_id/abc123"
}
```

## Migration Strategy

### Data Migration (if preserving old data)
- Export users from Scala MongoDB
- Convert BSON format to Python format
- Import into new database
- Preserve ELO ratings

### Gradual Cutover (optional)
- Run both servers in parallel
- Route new games to Python
- Keep Scala for existing games
- Full cutover after validation

## Testing Strategy

### Unit Tests
- All model methods
- Game logic (move processing)
- ELO calculations
- Board operations

### Integration Tests
- Full game simulation (training mode)
- Arena matching (4 bots)
- API endpoint workflows
- Database persistence

### Comparison Tests
- Run identical game sequences in both Scala & Python
- Compare final states
- Verify deterministic behavior

## Risk Mitigation

### High-Risk Areas
1. **Game Logic Bugs**: Subtle differences in move processing could affect gameplay
   - Mitigation: Extensive comparison tests, side-by-side validation
2. **Performance**: Python may be slower than Scala
   - Mitigation: Async I/O, profiling, caching
3. **Concurrency**: Managing multiple simultaneous games
   - Mitigation: Proper async/await usage, connection pooling

## Success Criteria

- [ ] All training mode games work correctly
- [ ] Arena matching creates balanced games
- [ ] No game logic regressions vs Scala version
- [ ] API response times < 100ms (excluding bot think time)
- [ ] Client UI fully functional
- [ ] 100+ concurrent games supported
- [ ] Comprehensive test coverage (>80%)

## Timeline Summary
- **Week 1**: Models + Game Logic (Phase 1-2)
- **Week 2**: Database + API (Phase 3-4)
- **Week 3**: System Components + Client (Phase 5-6)
- **Week 4**: Testing + Deployment (Phase 7-8)

**Total Estimated Effort**: 23 working days (~4-5 weeks with buffer)
