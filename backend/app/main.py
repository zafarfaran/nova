"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import audit, chaser, chat, clients, documents, evidence, validation, vat_periods
from app.config import get_settings

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


# Include routers
app.include_router(clients.router, prefix="/api/v1")
app.include_router(vat_periods.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(chaser.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
