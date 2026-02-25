"""Alembic migration environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, create_engine

from app.config import get_settings
from app.models.shared import Base

# Import all models here so they are registered with Base.metadata
from app.models.chaser import ChaserRequest, ChaserResponse  # noqa: F401
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.clients import Client  # noqa: F401
from app.models.documents import Document  # noqa: F401
from app.models.validation import ValidationResult  # noqa: F401

# New enterprise schema models
from app.models.clients import ClientContact  # noqa: F401
from app.models.engagements import Engagement  # noqa: F401
from app.models.documents import DocumentCategory, DocumentType  # noqa: F401
from app.models.documents import FileObject  # noqa: F401
from app.models.documents import DocumentVersion  # noqa: F401
from app.models.clients import Counterparty  # noqa: F401
from app.models.clients import FinancialAccount  # noqa: F401
from app.models.requests import RequestSet  # noqa: F401
from app.models.requests import RequestItem  # noqa: F401
from app.models.requests import RequestTemplate, RequestTemplateItem  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401

# Helio tax planning models
from app.models.tax import (  # noqa: F401
    TaxProfile,
    TaxObservation,
    TaxMeetingNote,
    TaxConversation,
    TaxMessage,
    TaxContextSnippet,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
database_url = settings.get_database_url()

# Escape % characters for configparser (required for URL-encoded passwords)
# Only set this for non-Supabase connections since we create engine directly for Supabase
if not settings.is_supabase:
    escaped_url = database_url.replace("%", "%%")
    config.set_main_option("sqlalchemy.url", escaped_url)

# Build connect_args for Supabase SSL
connect_args = {}
if settings.is_supabase and settings.supabase_ssl_mode and settings.supabase_ssl_mode != "disable":
    connect_args["sslmode"] = settings.supabase_ssl_mode


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Create engine with SSL support for Supabase
    if settings.is_supabase and connect_args:
        connectable = create_engine(
            database_url,
            poolclass=pool.NullPool,
            connect_args=connect_args,
        )
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
