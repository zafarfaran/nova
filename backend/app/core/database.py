"""Database session and engine configuration."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from app.config import get_settings

settings = get_settings()

# Build engine kwargs based on database type
engine_kwargs: dict = {"echo": settings.debug and not settings.is_sqlite}

if settings.is_sqlite:
    # SQLite-specific settings
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif settings.is_supabase:
    # Supabase/PostgreSQL-specific settings with SSL
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300  # Recycle connections every 5 minutes
    
    # SSL configuration for Supabase
    connect_args = {}
    if settings.supabase_ssl_mode and settings.supabase_ssl_mode != "disable":
        connect_args["sslmode"] = settings.supabase_ssl_mode
    
    if connect_args:
        engine_kwargs["connect_args"] = connect_args
else:
    # Standard PostgreSQL settings
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.get_database_url(), **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
