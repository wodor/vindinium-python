# Vindinium - Python Implementation

A Python rewrite of the Vindinium game server (originally written in Scala/Play Framework).

## Overview

Vindinium is a multiplayer AI programming challenge where players control heroes that:
- Navigate a grid-based map
- Capture and defend gold mines
- Drink beer at taverns to restore health
- Fight each other for control of resources
- Accumulate gold to win

## Requirements

- Python 3.11+
- MongoDB 4.4+
- pip

## Installation

```bash
cd python
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=vindinium
SECRET_KEY=your-secret-key-here
HOST=localhost
PORT=9000
```

## Running

```bash
python main.py
```

Server will start on `http://localhost:9000`

## Project Structure

- `vindinium/models/` - Core data models (Game, Hero, Board, etc.)
- `vindinium/game_logic/` - Game rules and mechanics
- `vindinium/api/` - REST API endpoints
- `vindinium/db/` - Database layer
- `vindinium/system/` - System components (ELO, replays, matchmaking)
- `tests/` - Test suite

## API Endpoints

### Training Mode
```bash
POST /api/training
Content-Type: application/x-www-form-urlencoded

key=YOUR_API_KEY&turns=100&map=m1
```

### Arena Mode
```bash
POST /api/arena
Content-Type: application/x-www-form-urlencoded

key=YOUR_API_KEY
```

### Make Move
```bash
POST /api/{gameId}/{token}/{dir}

dir: North, South, East, West, or Stay
```

## Development Status

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed roadmap.

## Manual Testing

For manual testing and debugging of the client integration, see [MANUAL_TESTING.md](MANUAL_TESTING.md). This guide covers:
- Running the game server with proper process management
- Building and serving the JavaScript client
- Debugging common issues (port conflicts, MongoDB readiness, etc.)
- Best practices for manual testing vs CI/automated testing

## Testing

### Unit Tests

Run unit tests for individual components:

```bash
pytest tests/unit/ -v
```

### Integration Tests

Run integration tests:

```bash
pytest tests/integration/ -v
```

### End-to-End Tests

Run full end-to-end tests with MongoDB container and live server:

```bash
# Simple way - runs everything automatically
./run_e2e_tests.sh

# Or using Python directly
python run_e2e_tests.py

# Run specific E2E tests
./run_e2e_tests.sh -k test_health

# Run with verbose output
./run_e2e_tests.sh -vv
```

The E2E test suite automatically:
- ✅ Starts MongoDB container using Docker
- ✅ Starts the game server
- ✅ Runs comprehensive API tests
- ✅ Cleans up all resources (even on Ctrl+C)

**Prerequisites for E2E tests:**
- Docker or Podman installed
- Python 3.10+
- All dependencies installed (`pip install -r requirements.txt`)

See [tests/e2e/README.md](tests/e2e/README.md) for detailed E2E testing documentation.

### All Tests

Run all tests:

```bash
pytest tests/ -v
```

## Original Scala Version

The original Scala implementation is in the parent directory. This Python version aims to be functionally equivalent while leveraging Python's async capabilities and modern web framework features.

## License

Same as original Vindinium project (see LICENSE in root directory)
