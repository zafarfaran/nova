"""FastAPI middleware for request tracking and metrics."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.metrics import (
    active_requests,
    http_request_duration,
    http_requests_total,
    request_size_bytes,
    response_size_bytes,
)
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP requests with metrics and tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get endpoint (simplified - use path)
        endpoint = request.url.path
        method = request.method
        
        # Determine section from endpoint path
        section = "api"
        if "/documents" in endpoint:
            section = "document_processing"
        elif "/chat" in endpoint:
            section = "chat"
        elif "/validation" in endpoint:
            section = "validation"
        elif "/chaser" in endpoint or "/email" in endpoint:
            section = "email"
        elif "/clients" in endpoint or "/engagements" in endpoint:
            section = "client_management"
        
        # Format source as endpoint path
        source = f"{method}:{endpoint}"
        
        # Track active requests
        active_requests.inc()
        
        # Get request size (approximate)
        request_size = 0
        if hasattr(request, "_body"):
            request_size = len(request._body) if request._body else 0
        
        start_time = time.time()
        
        with tracer.start_as_current_span(
            f"http.{method}",
            attributes={
                "http.method": method,
                "http.url": str(request.url),
                "http.route": endpoint,
                "request.id": request_id,
            }
        ):
            try:
                response = await call_next(request)
                
                duration = time.time() - start_time
                status_code = response.status_code
                
                # Always record metrics (metrics always run)
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    section=section,
                    source=source,
                ).inc()
                
                http_request_duration.labels(
                    method=method,
                    endpoint=endpoint,
                    section=section,
                    source=source,
                ).observe(duration)
                
                if request_size > 0:
                    request_size_bytes.labels(
                        method=method,
                        endpoint=endpoint,
                        section=section,
                        source=source,
                    ).observe(request_size)
                
                # Get response size - prefer Content-Length header, avoid buffering streaming responses
                response_size = 0
                content_length = response.headers.get("content-length")
                
                # Check if this is a streaming response
                is_streaming = (
                    response.headers.get("transfer-encoding") == "chunked"
                    or "text/event-stream" in (response.media_type or "")
                    or status_code in (206, 304)  # Partial content, Not Modified
                )
                
                if content_length:
                    # Use Content-Length header if available (no need to read body)
                    try:
                        response_size = int(content_length)
                        response_size_bytes.labels(
                            method=method,
                            endpoint=endpoint,
                            section=section,
                            source=source,
                        ).observe(response_size)
                    except (ValueError, TypeError):
                        pass
                    # Return original response without consuming body
                    return response
                elif is_streaming:
                    # Skip size measurement for streaming responses
                    # Return original response without consuming body
                    return response
                else:
                    # Only buffer small, non-streaming responses for size measurement
                    # Limit to reasonable size to avoid memory issues (e.g., 1MB)
                    MAX_BODY_SIZE_FOR_MEASUREMENT = 1024 * 1024  # 1MB
                    response_body = b""
                    body_collected = False
                    try:
                        async for chunk in response.body_iterator:
                            response_body += chunk
                            if len(response_body) > MAX_BODY_SIZE_FOR_MEASUREMENT:
                                # Stop collecting if too large, return original response
                                body_collected = False
                                break
                        else:
                            # Completed iteration - got full body
                            body_collected = True
                            response_size = len(response_body)
                    except Exception:
                        # If body collection fails, return original response
                        body_collected = False
                    
                    if body_collected and response_body:
                        # Record size and return rebuilt response
                        response_size_bytes.labels(
                            method=method,
                            endpoint=endpoint,
                            section=section,
                            source=source,
                        ).observe(response_size)
                        return Response(
                            content=response_body,
                            status_code=status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type,
                        )
                    else:
                        # Return original response (too large or collection failed)
                        return response
                
            except Exception as e:
                duration = time.time() - start_time
                status_code = 500
                
                # Always record error metric (metrics always run)
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    section=section,
                    source=source,
                ).inc()
                
                raise
            
            finally:
                active_requests.dec()
