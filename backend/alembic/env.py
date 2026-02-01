"""Alembic migration environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, create_engine

from app.config import get_settings
from app.models.base import Base

# Import all models here so they are registered with Base.metadata
from app.models.chaser import ChaserRequest, ChaserResponse  # noqa: F401
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.validation import ValidationResult  # noqa: F401

# New enterprise schema models
from app.models.client_contact import ClientContact  # noqa: F401
from app.models.engagement import Engagement  # noqa: F401
from app.models.document_type import DocumentCategory, DocumentType  # noqa: F401
from app.models.file_object import FileObject  # noqa: F401
from app.models.document_version import DocumentVersion  # noqa: F401
from app.models.counterparty import Counterparty  # noqa: F401
from app.models.financial_account import FinancialAccount  # noqa: F401
from app.models.request_set import RequestSet  # noqa: F401
from app.models.request_item import RequestItem  # noqa: F401
from app.models.request_template import RequestTemplate, RequestTemplateItem  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

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
