"""E2E tests for game creation and basic gameplay."""

import pytest
import httpx


@pytest.mark.asyncio
class TestGameCreation:
    """Test game creation via API."""
    
    async def test_create_training_game_default(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test creating a training game with default parameters."""
        response = await http_client.post(
            "/api/training",
            data={
                "key": "test-api-key",
            },
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "game" in data
        assert "hero" in data
        assert "token" in data
        assert "viewUrl" in data
        assert "playUrl" in data
        
        # Validate game data
        game = data["game"]
        assert "id" in game
        assert game["id"].startswith("training-")
        assert game["max_turns"] == 300  # Default
        assert game["turn"] == 0
        assert game["status"] != "FINISHED"  # Game should not be finished
        
        # Validate hero data
        hero = data["hero"]
        assert hero["id"] == 1
        assert hero["life"] == 100
        assert hero["gold"] == 0
        assert "pos" in hero
    
    async def test_create_training_game_custom_turns(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test creating a training game with custom turn count."""
        response = await http_client.post(
            "/api/training",
            data={
                "key": "test-api-key",
                "turns": 100,
            },
        )
        assert response.status_code == 200
        data = response.json()
        
        game = data["game"]
        assert game["max_turns"] == 100
    
    async def test_create_training_game_invalid_turns(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test that creating a game with invalid turns returns 400."""
        response = await http_client.post(
            "/api/training",
            data={
                "key": "test-api-key",
                "turns": 2000,  # Too many
            },
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestGameMovement:
    """Test hero movement mechanics via API."""
    
    async def test_make_move_stay(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test making a Stay move."""
        # Create a game
        create_response = await http_client.post(
            "/api/training",
            data={"key": "test-api-key"},
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        game_id = create_data["game"]["id"]
        token = create_data["token"]
        initial_pos = create_data["hero"]["pos"]
        
        # Make a Stay move
        move_response = await http_client.post(
            f"/api/{game_id}/{token}/Stay"
        )
        assert move_response.status_code == 200
        move_data = move_response.json()
        
        # Hero should stay in the same position
        new_pos = move_data["hero"]["pos"]
        assert new_pos == initial_pos
        
        # Game should advance one turn
        assert move_data["game"]["turn"] == 1
    
    async def test_move_with_invalid_token(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test that moving with an invalid token returns 403."""
        # Create a game
        create_response = await http_client.post(
            "/api/training",
            data={"key": "test-api-key"},
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        game_id = create_data["game"]["id"]
        
        # Try to move with invalid token
        move_response = await http_client.post(
            f"/api/{game_id}/invalid-token/Stay"
        )
        assert move_response.status_code == 403
    
    async def test_move_nonexistent_game(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test that moving in a nonexistent game returns 404."""
        move_response = await http_client.post(
            "/api/nonexistent-game/some-token/Stay"
        )
        assert move_response.status_code == 404
    
    async def test_sequential_moves(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test making a move and checking game state updates."""
        # Create a game
        create_response = await http_client.post(
            "/api/training",
            data={"key": "test-api-key"},
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        game_id = create_data["game"]["id"]
        token = create_data["token"]
        initial_turn = create_data["game"]["turn"]
        
        # Make one Stay move
        move_response = await http_client.post(
            f"/api/{game_id}/{token}/Stay"
        )
        assert move_response.status_code == 200
        move_data = move_response.json()
        # Turn should advance
        assert move_data["game"]["turn"] == initial_turn + 1


@pytest.mark.asyncio
class TestGameState:
    """Test game state retrieval via API."""
    
    async def test_get_game_state(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test retrieving game state."""
        # Create a game
        create_response = await http_client.post(
            "/api/training",
            data={"key": "test-api-key"},
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        game_id = create_data["game"]["id"]
        
        # Get game state
        state_response = await http_client.get(f"/api/game/{game_id}")
        assert state_response.status_code == 200
        state_data = state_response.json()
        
        assert "game" in state_data
        assert state_data["game"]["id"] == game_id
    
    async def test_get_nonexistent_game(
        self, http_client: httpx.AsyncClient, clean_database
    ):
        """Test that getting a nonexistent game returns 404."""
        state_response = await http_client.get("/api/game/nonexistent-game")
        assert state_response.status_code == 404
