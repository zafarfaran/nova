"""Alembic migration environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.models.base import Base

# Import all models here so they are registered with Base.metadata
from app.models.audit import AuditTrailEntry  # noqa: F401
from app.models.chaser import ChaserRequest, ChaserResponse  # noqa: F401
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.evidence import EvidenceItem  # noqa: F401
from app.models.validation import ValidationResult  # noqa: F401
from app.models.vat_period import VATPeriod  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.get_database_url())


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
