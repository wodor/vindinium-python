"""E2E tests for basic game server functionality."""

import pytest
import httpx


@pytest.mark.asyncio
class TestBasicServerHealth:
    """Test that the server is running and responding."""
    
    async def test_health_endpoint(self, http_client: httpx.AsyncClient):
        """Test that the health endpoint returns 200 OK."""
        response = await http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    async def test_root_endpoint(self, http_client: httpx.AsyncClient):
        """Test that the root endpoint returns HTML."""
        response = await http_client.get("/")
        assert response.status_code == 200
        assert "Vindinium" in response.text
