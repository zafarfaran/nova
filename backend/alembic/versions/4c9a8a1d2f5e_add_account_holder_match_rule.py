"""Add ACCOUNT_HOLDER_MATCH to ruletype enum

Revision ID: 4c9a8a1d2f5e
Revises: 8b2b6d7f1a3c
Create Date: 2026-01-25 05:35:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c9a8a1d2f5e"
down_revision: Union[str, None] = "8b2b6d7f1a3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("ALTER TYPE ruletype ADD VALUE IF NOT EXISTS 'ACCOUNT_HOLDER_MATCH'")


def downgrade() -> None:
    # PostgreSQL enums cannot easily remove values; leave as no-op.
    pass
