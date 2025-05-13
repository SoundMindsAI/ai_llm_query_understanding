"""
Middleware components for the LLM Query Understanding Service.

This module provides middleware for request logging, performance monitoring,
and error handling.
"""
import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from llm_query_understand.utils.logging_config import (
    get_logger, set_request_context, 
    clear_request_context, log_request,
    sanitize_data
)

logger = get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response details and adding correlation IDs."""
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None) -> None:
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            exclude_paths: List of paths to exclude from logging (e.g., health checks)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/readiness", "/metrics"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, add correlation ID, and log details.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response
        """
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Set up request context with correlation ID
        set_request_context(request_id=request_id)
        
        # Capture start time for performance measurement
        start_time = time.time()
        
        # Get request details for logging
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params) if request.query_params else None
        
        # Extract relevant headers (exclude potential sensitive data)
        safe_headers = {
            k: v for k, v in request.headers.items()
            if k.lower() in ["user-agent", "content-type", "accept"]
        }
        
        # Extract request body if available
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # Clone the request to avoid consuming it
                body_bytes = await request.body()
                # Reset the request body for the endpoint handler
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
                
                # Attempt to parse as JSON
                if "application/json" in request.headers.get("content-type", ""):
                    try:
                        body = await request.json()
                    except:
                        # If not parseable as JSON, use raw content
                        body = {"raw": body_bytes.decode("utf-8", errors="ignore")}
            except Exception as e:
                logger.warning(f"Error accessing request body: {str(e)}")
        
        # Log the incoming request
        log_request(
            method=method,
            path=path,
            query_params=query_params,
            headers=safe_headers,
            body=body
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log the response
            log_request(
                method=method,
                path=path,
                status_code=response.status_code,
                response_time=response_time
            )
            
            return response
            
        except Exception as e:
            # Log any unhandled exceptions
            logger.error(
                f"Unhandled exception during request processing: {str(e)}",
                exc_info=True,
                extra={
                    "path": path,
                    "method": method,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
            )
            raise
        finally:
            # Always clear request context
            clear_request_context()


class ResponseTimeHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a response time header to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add X-Response-Time header.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response with added headers
        """
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # Add the response time header (in milliseconds)
        response.headers["X-Response-Time"] = f"{response_time * 1000:.2f}ms"
        
        return response
