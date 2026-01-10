"""Game viewing routes with SSE support."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from vindinium.db.repositories import GameRepository, get_game_repository
from vindinium.api.sse_utils import game_state_stream, active_games_stream


router = APIRouter(tags=["game-viewer"])


@router.get("/events/{game_id}")
async def game_events(
    game_id: str,
    repo: GameRepository = Depends(get_game_repository),
):
    """
    Server-Sent Events endpoint for streaming game state updates.
    
    The client connects to this endpoint and receives real-time game state
    updates as the game progresses. Each event contains the full game state
    in JSON format.
    
    Args:
        game_id: Game identifier to stream
        repo: Game repository instance
        
    Returns:
        EventSourceResponse with game state stream
    """
    # Check if game exists
    game = await repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Return SSE stream
    return EventSourceResponse(game_state_stream(game_id, repo))


@router.get("/now-playing")
async def now_playing(
    repo: GameRepository = Depends(get_game_repository),
):
    """
    Server-Sent Events endpoint for streaming active games list.
    
    The client connects to this endpoint and receives updates about
    currently active (non-finished) games.
    
    Args:
        repo: Game repository instance
        
    Returns:
        EventSourceResponse with active games stream
    """
    return EventSourceResponse(active_games_stream(repo))


@router.get("/tv")
async def tv_mode(
    repo: GameRepository = Depends(get_game_repository),
):
    """
    TV mode viewer page that displays a random active game.
    
    This endpoint finds an active game and redirects to its viewer,
    or shows a message if no games are active.
    
    Args:
        repo: Game repository instance
        
    Returns:
        HTML page displaying game viewer or "no games" message
    """
    # Get recent active games
    games = await repo.get_active_games(limit=3)
    
    if not games:
        # No active games - show placeholder
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Vindinium TV</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .message {
            text-align: center;
            padding: 2rem;
            background-color: #2a2a2a;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        h1 {
            margin-bottom: 1rem;
        }
        p {
            color: #aaaaaa;
        }
    </style>
</head>
<body>
    <div class="message">
        <h1>📺 Vindinium TV</h1>
        <p>No active games at the moment.</p>
        <p>Start a new game to begin!</p>
    </div>
</body>
</html>
        """)
    
    # Find first non-finished game or use the first game
    game = next((g for g in games if not g.finished), games[0])
    
    # Render game viewer
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Vindinium TV - Game {game.id}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/assets/css/vindinium.css">
    <link rel="stylesheet" href="/assets/vendors/bundle.css">
</head>
<body>
    <div id="game"></div>
    <script>
        var GAME_ID = "{game.id}";
    </script>
    <script src="/assets/vendors/bundle.js"></script>
    <script src="/assets/js/bundle.js"></script>
</body>
</html>
    """)


@router.get("/{game_id}")
async def game_viewer(
    game_id: str,
    repo: GameRepository = Depends(get_game_repository),
):
    """
    Game viewer page for a specific game.
    
    This endpoint serves an HTML page that loads the JavaScript client
    and connects to the SSE endpoint to display the game in real-time.
    
    Args:
        game_id: Game identifier to display
        repo: Game repository instance
        
    Returns:
        HTML page with embedded game viewer
    """
    # Check if game exists
    game = await repo.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Render game viewer HTML
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Vindinium - Game {game_id}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/assets/css/vindinium.css">
    <link rel="stylesheet" href="/assets/vendors/bundle.css">
</head>
<body>
    <div id="game"></div>
    <script>
        var GAME_ID = "{game_id}";
    </script>
    <script src="/assets/vendors/bundle.js"></script>
    <script src="/assets/js/bundle.js"></script>
</body>
</html>
    """)
