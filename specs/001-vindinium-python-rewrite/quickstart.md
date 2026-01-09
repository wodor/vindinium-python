# Quickstart Guide

## Prerequisites
- Python 3.11 or higher
- MongoDB 4.4 or higher
- pip (Python package installer)

## Setup

1. **Clone and Enter Directory**:
   ```bash
   cd python
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   Copy `.env.example` to `.env` and adjust if necessary.
   ```bash
   cp .env.example .env
   ```
   *Note: Ensure `MONGODB_URI` points to your running MongoDB instance.*

## Running the Server

Start the development server with auto-reload:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

## Running Tests

Run the test suite (including property-based tests):
```bash
pytest
```

## Game Concepts
- **Training Mode**: Use the `/api/training` endpoint to play against bots.
- **Arena Mode**: Use `/api/arena` to match against other players.
- **Visualizer**: Visit `http://localhost:8000/game/{game_id}` to watch a game.
