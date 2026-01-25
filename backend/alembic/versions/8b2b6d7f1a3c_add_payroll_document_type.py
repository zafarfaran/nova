"""Add PAYROLL to documenttype enum

Revision ID: 8b2b6d7f1a3c
Revises: f821930e02d8
Create Date: 2026-01-25 05:30:00.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b2b6d7f1a3c"
down_revision: Union[str, None] = "f821930e02d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'PAYROLL'")


def downgrade() -> None:
    # PostgreSQL enums cannot easily remove values; leave as no-op.
    pass
