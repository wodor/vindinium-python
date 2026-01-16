"""Integration tests for middleware with API routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_app():
    """Create a test app without database dependency."""
    from fastapi import FastAPI, HTTPException
    from vindinium.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
    
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    @app.get("/api/test")
    async def test_endpoint():
        return {"status": "ok", "message": "test endpoint"}
    
    @app.get("/api/not-found")
    async def not_found():
        raise HTTPException(status_code=404, detail="Resource not found")
    
    @app.get("/api/server-error")
    async def server_error():
        # Simulate an unexpected error
        raise RuntimeError("Unexpected server error")
    
    return app


class TestMiddlewareWithAPIRoutes:
    """Test middleware integration with API routes."""
    
    def test_successful_request_has_request_id(self, test_app):
        """Test that successful API requests include request ID."""
        with TestClient(test_app) as client:
            response = client.get("/api/test")
            
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers
            
            request_id = response.headers["X-Request-ID"]
            assert len(request_id) == 36  # UUID format
            
            data = response.json()
            assert data["status"] == "ok"
    
    def test_http_exception_preserves_status_code(self, test_app):
        """Test that HTTPException status codes are preserved."""
        with TestClient(test_app) as client:
            response = client.get("/api/not-found")
            
            # Should still get 404, not 500
            assert response.status_code == 404
            
            data = response.json()
            assert data["detail"] == "Resource not found"
            
            # Request ID should still be present
            assert "X-Request-ID" in response.headers
    
    def test_server_error_returns_500(self, test_app):
        """Test that unexpected errors return 500 with request ID."""
        with TestClient(test_app, raise_server_exceptions=False) as client:
            response = client.get("/api/server-error")
            
            assert response.status_code == 500
            assert "X-Request-ID" in response.headers
            
            data = response.json()
            assert data["error"] == "Internal server error"
            assert "request_id" in data
            
            # Request ID should match header
            assert data["request_id"] == response.headers["X-Request-ID"]
    
    def test_multiple_requests_have_unique_ids(self, test_app):
        """Test that each request gets a unique request ID."""
        with TestClient(test_app) as client:
            response1 = client.get("/api/test")
            response2 = client.get("/api/test")
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            id1 = response1.headers["X-Request-ID"]
            id2 = response2.headers["X-Request-ID"]
            
            # Request IDs should be unique
            assert id1 != id2
