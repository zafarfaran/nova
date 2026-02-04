"""Add vat_scheme and sales_channels to clients

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-01-24 20:00:00.000000

This migration adds the missing vat_scheme and sales_channels columns
to the clients table that were defined in the model but missing from
previous migrations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add vat_scheme column (nullable, as defined in model)
    op.add_column('clients', sa.Column('vat_scheme', sa.String(50), nullable=True))
    
    # Add sales_channels column (ARRAY of strings, nullable, default empty list)
    op.add_column('clients', sa.Column('sales_channels', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'))


def downgrade() -> None:
    # Drop columns in reverse order
    op.drop_column('clients', 'sales_channels')
    op.drop_column('clients', 'vat_scheme')
