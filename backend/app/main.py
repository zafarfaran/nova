"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.v1 import audit, chaser, chat, clients, documents, email, engagements, requests, validation
from app.config import get_settings
from app.core.logging import setup_structured_logging
from app.core.metrics import get_metrics
from app.core.middleware import RequestTrackingMiddleware

# Setup structured logging before anything else
settings = get_settings()
setup_structured_logging(debug=settings.debug)

app = FastAPI(
    title=settings.app_name,
    description="AI-powered document processing for UK VAT compliance",
    version="0.1.0",
)

# Request tracking middleware (must be before CORS)
app.add_middleware(RequestTrackingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics()


import logging

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event() -> None:
    """Log startup information."""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AI Provider: {settings.ai_provider}")
    logger.info(f"Storage Provider: {settings.storage_provider}")
    logger.info("=" * 60)


# Include routers
app.include_router(clients.router, prefix="/api/v1")
app.include_router(engagements.router, prefix="/api/v1")
app.include_router(requests.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(chaser.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(email.router, prefix="/api/v1")
