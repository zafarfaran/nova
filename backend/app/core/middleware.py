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
                
                # Get response size
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                if response_body:
                    response_size_bytes.labels(
                        method=method,
                        endpoint=endpoint,
                        section=section,
                        source=source,
                    ).observe(len(response_body))
                
                # Recreate response with body
                return Response(
                    content=response_body,
                    status_code=status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
                
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
