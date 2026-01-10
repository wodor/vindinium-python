"""Error handling and logging middleware."""

import logging
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vindinium")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Handle requests and catch exceptions."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log request
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"- {response.status_code} - {process_time:.3f}s"
            )
            
            return response
            
        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} "
                f"- ERROR: {str(exc)} - {process_time:.3f}s",
                exc_info=True
            )
            
            # Return error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "detail": str(exc) if logger.level == logging.DEBUG else "An error occurred"
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Log request details."""
        logger.debug(f"Incoming request: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
        response = await call_next(request)
        
        logger.debug(f"Response status: {response.status_code}")
        
        return response
