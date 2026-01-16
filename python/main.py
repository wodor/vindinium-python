"""Vindinium game server entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from vindinium.config import settings
from vindinium.db.mongodb import MongoDBClient
from vindinium.api.routes import router as api_router
from vindinium.api.game_routes import router as game_router
from vindinium.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)."""
    # Startup: Connect to MongoDB
    await MongoDBClient.connect()
    try:
        # Create indexes
        from vindinium.db.repositories import GameRepository
        db = MongoDBClient.get_database()
        repo = GameRepository(db)
        await repo.create_indexes()
    except Exception as e:
        print(f"Warning: Could not create indexes: {e}")
    
    yield
    
    # Shutdown: Disconnect from MongoDB
    await MongoDBClient.disconnect()


app = FastAPI(
    title="Vindinium",
    description="AI Programming Challenge Game Server - Python Implementation",
    version="2.0.0",
    lifespan=lifespan,
)

# Add middleware (executed in reverse order of registration)
# RequestLoggingMiddleware is added last so ErrorHandlingMiddleware runs first
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Mount static files for client assets
# Check if public directory exists (from repository root)
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/assets", StaticFiles(directory=public_dir), name="assets")

# Include API routes
app.include_router(api_router)
app.include_router(game_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page."""
    return """
    <html>
        <head><title>Vindinium - Python Edition</title></head>
        <body>
            <h1>Vindinium - Python Edition</h1>
            <p>Game server is running!</p>
            <p>This is a Python rewrite of the original Scala Vindinium server.</p>
            <p>API endpoints will be available at:</p>
            <ul>
                <li>POST /api/move/{game_id} - Make a move in a game</li>
                <li>GET /api/game/{game_id} - Get game state</li>
                <li>POST /api/game/create - Create a new game</li>
            </ul>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


def main():
    """Main entry point for the application."""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
