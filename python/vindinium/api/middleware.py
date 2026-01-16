"""Error handling and logging middleware."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vindinium")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling.
    
    This middleware catches unhandled exceptions and converts them to
    appropriate JSON error responses. It also logs all errors with
    context information.
    
    Note: HTTPException and RequestValidationError are handled by FastAPI's
    built-in exception handlers, so we don't intercept them here.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Handle requests and catch exceptions.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain
            
        Returns:
            Response object (success or error)
        """
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log successful request
            process_time = time.time() - start_time
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- {response.status_code} - {process_time:.3f}s"
            )
            
            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except HTTPException:
            # Re-raise HTTPException to let FastAPI handle it
            # (FastAPI has built-in handlers for proper status codes)
            raise
            
        except RequestValidationError:
            # Re-raise validation errors to let FastAPI handle them
            raise
            
        except Exception as exc:
            # Log unexpected errors with full stack trace
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- ERROR: {type(exc).__name__}: {str(exc)} "
                f"- {process_time:.3f}s",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                }
            )
            
            # Return generic error response (don't leak internal details)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "detail": str(exc) if logger.level == logging.DEBUG else "An unexpected error occurred",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request logging.
    
    Logs request details including headers, client info, and request body
    for debugging purposes. Due to middleware execution order, this runs
    after ErrorHandlingMiddleware, so request_id is available.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Log detailed request information.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain
            
        Returns:
            Response from the next handler
        """
        # Get request ID (set by ErrorHandlingMiddleware which runs first)
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Log incoming request details at DEBUG level
        logger.debug(
            f"[{request_id}] Incoming request: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        
        # Log headers (excluding sensitive ones)
        if logger.level <= logging.DEBUG:
            safe_headers = {
                k: v for k, v in request.headers.items()
                if k.lower() not in ["authorization", "cookie", "x-api-key"]
            }
            logger.debug(f"[{request_id}] Headers: {safe_headers}")
        
        # Process request through the rest of the middleware chain
        response = await call_next(request)
        
        # Log response status
        logger.debug(
            f"[{request_id}] Response status: {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
            }
        )
        
        return response
