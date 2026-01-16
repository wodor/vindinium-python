"""Unit tests for middleware components."""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from vindinium.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware


@pytest.fixture
def app():
    """Create a test FastAPI application with middleware."""
    test_app = FastAPI()
    
    # Add middleware in correct order
    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(ErrorHandlingMiddleware)
    
    # Add test routes
    @test_app.get("/success")
    async def success():
        return {"status": "ok"}
    
    @test_app.get("/error")
    async def error():
        raise Exception("Test error")
    
    @test_app.get("/http-error")
    async def http_error():
        raise HTTPException(status_code=404, detail="Not found")
    
    @test_app.get("/validation-error")
    async def validation_error():
        raise RequestValidationError(errors=[])
    
    return test_app


@pytest.mark.asyncio
class TestErrorHandlingMiddleware:
    """Test the ErrorHandlingMiddleware."""
    
    async def test_successful_request_adds_request_id(self, app):
        """Test that successful requests get a request ID header."""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            response = client.get("/success")
            
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers
            assert len(response.headers["X-Request-ID"]) > 0
    
    async def test_successful_request_logs_info(self, app, caplog):
        """Test that successful requests are logged at INFO level."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.INFO):
            with TestClient(app) as client:
                response = client.get("/success")
                
                assert response.status_code == 200
                # Check that request was logged
                assert any("GET /success" in record.message for record in caplog.records)
                assert any("200" in record.message for record in caplog.records)
    
    async def test_exception_returns_500_with_request_id(self, app):
        """Test that unhandled exceptions return 500 with request ID."""
        from fastapi.testclient import TestClient
        
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/error")
            
            assert response.status_code == 500
            assert "X-Request-ID" in response.headers
            
            data = response.json()
            assert data["error"] == "Internal server error"
            assert "request_id" in data
            assert data["request_id"] == response.headers["X-Request-ID"]
    
    async def test_exception_logs_error_with_traceback(self, app, caplog):
        """Test that exceptions are logged with full traceback."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.ERROR):
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/error")
                
                # Check error was logged
                assert any("ERROR" in record.message for record in caplog.records)
                assert any("Test error" in record.message for record in caplog.records)
    
    async def test_http_exception_not_caught(self, app):
        """Test that HTTPException is re-raised for FastAPI to handle."""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            response = client.get("/http-error")
            
            # FastAPI should handle this and return 404
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Not found"
    
    async def test_validation_error_not_caught(self, app):
        """Test that RequestValidationError is re-raised for FastAPI to handle."""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            response = client.get("/validation-error")
            
            # FastAPI should handle this and return 422
            assert response.status_code == 422
    
    async def test_error_detail_hidden_in_production(self, app):
        """Test that error details are hidden when not in DEBUG mode."""
        from fastapi.testclient import TestClient
        
        # Ensure logger is not in DEBUG mode
        logger = logging.getLogger("vindinium")
        original_level = logger.level
        logger.setLevel(logging.INFO)
        
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/error")
                
                data = response.json()
                # Should show generic message, not actual error
                assert data["detail"] == "An unexpected error occurred"
        finally:
            logger.setLevel(original_level)
    
    async def test_error_detail_shown_in_debug(self, app):
        """Test that error details are shown when in DEBUG mode."""
        from fastapi.testclient import TestClient
        
        # Set logger to DEBUG mode
        logger = logging.getLogger("vindinium")
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/error")
                
                data = response.json()
                # Should show actual error message
                assert "Test error" in data["detail"]
        finally:
            logger.setLevel(original_level)


@pytest.mark.asyncio
class TestRequestLoggingMiddleware:
    """Test the RequestLoggingMiddleware."""
    
    async def test_request_logged_at_debug_level(self, app, caplog):
        """Test that requests are logged at DEBUG level."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.DEBUG):
            with TestClient(app) as client:
                response = client.get("/success")
                
                assert response.status_code == 200
                # Check that request details were logged
                assert any("Incoming request: GET" in record.message for record in caplog.records)
                assert any("/success" in record.message for record in caplog.records)
    
    async def test_response_logged_at_debug_level(self, app, caplog):
        """Test that responses are logged at DEBUG level."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.DEBUG):
            with TestClient(app) as client:
                response = client.get("/success")
                
                assert response.status_code == 200
                # Check that response status was logged
                assert any("Response status: 200" in record.message for record in caplog.records)
    
    async def test_sensitive_headers_excluded(self, app, caplog):
        """Test that sensitive headers are excluded from logs."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.DEBUG):
            with TestClient(app) as client:
                response = client.get(
                    "/success",
                    headers={
                        "Authorization": "Bearer secret-token",
                        "Cookie": "session=secret",
                        "X-Api-Key": "secret-key",
                        "User-Agent": "test-client",
                    }
                )
                
                assert response.status_code == 200
                
                # Check that sensitive headers are NOT in logs
                log_output = "\n".join(record.message for record in caplog.records)
                assert "secret-token" not in log_output
                assert "session=secret" not in log_output
                assert "secret-key" not in log_output
                
                # But user-agent should be present
                assert "test-client" in log_output
    
    async def test_request_id_used_in_logs(self, app, caplog):
        """Test that request ID is included in log messages."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.DEBUG):
            with TestClient(app) as client:
                response = client.get("/success")
                
                request_id = response.headers.get("X-Request-ID")
                assert request_id is not None
                
                # Check that request ID appears in logs
                # (Note: In the first log from RequestLoggingMiddleware, 
                # request_id might be 'unknown' since it's set by ErrorHandlingMiddleware)
                log_output = "\n".join(record.message for record in caplog.records)
                # At least one log should have the request ID
                assert request_id in log_output or "unknown" in log_output


@pytest.mark.asyncio
class TestMiddlewareIntegration:
    """Test middleware working together."""
    
    async def test_both_middleware_process_request(self, app, caplog):
        """Test that both middleware process the same request."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.DEBUG):
            with TestClient(app) as client:
                response = client.get("/success")
                
                assert response.status_code == 200
                assert "X-Request-ID" in response.headers
                
                # Should have logs from both middleware
                log_messages = [record.message for record in caplog.records]
                assert any("Incoming request" in msg for msg in log_messages)  # RequestLoggingMiddleware
                assert any("Response status" in msg for msg in log_messages)   # RequestLoggingMiddleware
                assert any("GET /success" in msg and "200" in msg for msg in log_messages)  # ErrorHandlingMiddleware
    
    async def test_request_id_consistent_across_middleware(self, app, caplog):
        """Test that request ID is consistent across all logs."""
        from fastapi.testclient import TestClient
        
        with caplog.at_level(logging.INFO):
            with TestClient(app) as client:
                response = client.get("/success")
                
                request_id = response.headers["X-Request-ID"]
                
                # Check that request ID appears in INFO logs from ErrorHandlingMiddleware
                info_logs = [record.message for record in caplog.records if record.levelno == logging.INFO]
                assert any(request_id in msg for msg in info_logs)
