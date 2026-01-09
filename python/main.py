"""Vindinium game server entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from vindinium.config import settings

app = FastAPI(
    title="Vindinium",
    description="AI Programming Challenge Game Server - Python Implementation",
    version="2.0.0",
)

# TODO: Add API routes when implemented
# from vindinium.api import routes
# app.include_router(routes.router)


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
