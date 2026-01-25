"""FastAPI application entry point."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import audit, chaser, chat, clients, documents, evidence, validation, vat_periods
from app.config import get_settings

# Configure logging
def setup_logging() -> None:
    """Configure logging for the application."""
    # Get root logger
    root_logger = logging.getLogger()

    # Set level based on debug setting (app logs can be debug, root stays quiet)
    settings = get_settings()
    app_log_level = logging.DEBUG if settings.debug else logging.INFO
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set specific loggers
    for logger_name in [
        "app",
        "app.tasks",
        "app.services",
        "app.ai",
    ]:
        logging.getLogger(logger_name).setLevel(app_log_level)

    # Always show extraction pipeline details
    logging.getLogger("app.tasks.document_tasks").setLevel(logging.INFO)
    logging.getLogger("app.services.pdf_extraction_service").setLevel(logging.INFO)
    logging.getLogger("app.ai.openai_provider").setLevel(logging.INFO)
    logging.getLogger("app.ai.anthropic_provider").setLevel(logging.INFO)

    # Reduce noise from some libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)

    logging.info("Logging configured successfully")


# Setup logging before anything else
setup_logging()

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered document processing for UK VAT compliance",
    version="0.1.0",
)

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
app.include_router(vat_periods.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(chaser.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
