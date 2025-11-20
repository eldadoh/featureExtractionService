"""
FastAPI middleware for request logging and error handling.

Middleware:
    - RequestLoggingMiddleware: Logs all requests with timing
    - ErrorHandlingMiddleware: Catches and formats exceptions

Features:
    - Request/response timing
    - Correlation IDs
    - Structured logging
    - Standardized error responses
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging_config import get_logger
from core.exceptions import FeatureDetectionException
from models.responses import ErrorResponse

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses.
    
    Logs:
        - Request method, path, headers
        - Response status code, size
        - Processing time
        - Request ID for tracing
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
        
        Returns:
            Response from handler
        """
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        
        # Log incoming request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unexpected errors
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=processing_time
            )
            raise
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Log completed request
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            processing_time_ms=processing_time
        )
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time-Ms"] = f"{processing_time:.2f}"
        
        return response


async def custom_exception_handler(request: Request, exc: FeatureDetectionException) -> JSONResponse:
    """
    Handle custom exceptions and return standardized error response.
    
    Args:
        request: FastAPI request
        exc: Custom exception
    
    Returns:
        JSON response with error details
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "Request failed with known exception",
        request_id=request_id,
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Unexpected exception
    
    Returns:
        JSON response with generic error
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "Request failed with unexpected exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True
    )
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )

