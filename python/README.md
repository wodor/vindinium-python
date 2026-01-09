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

## Testing

```bash
pytest tests/
```

## Original Scala Version

The original Scala implementation is in the parent directory. This Python version aims to be functionally equivalent while leveraging Python's async capabilities and modern web framework features.

## License

Same as original Vindinium project (see LICENSE in root directory)
