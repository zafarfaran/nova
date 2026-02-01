"""Drop deprecated tables and columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-01 13:00:00.000000

This migration removes deprecated tables and columns:
- Drops vat_periods table (replaced by engagements)
- Drops evidence_items table (replaced by request_sets/request_items)
- Drops checklist_items table (replaced by request_sets/request_items)
- Drops audit_trail_entries table (replaced by audit_logs)
- Removes evidence_item_id, document_type, extracted_data from documents
- Updates chaser_requests to use engagement_id instead of vat_period_id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make client_id required on documents (was nullable for backwards compat)
    op.alter_column('documents', 'client_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    # Remove legacy columns from documents (if they exist)
    # These may not exist if migrating from fresh schema
    try:
        op.drop_constraint('documents_evidence_item_id_fkey', 'documents', type_='foreignkey')
    except Exception:
        pass  # Constraint may not exist
    
    # Use raw SQL to drop columns only if they exist
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS evidence_item_id")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_type")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS extracted_data")
    
    # Update chaser_requests: add engagement_id, remove vat_period_id
    # First check if engagement_id already exists
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE chaser_requests ADD COLUMN engagement_id INTEGER;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    
    # Create foreign key if not exists
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE chaser_requests 
            ADD CONSTRAINT fk_chaser_requests_engagement_id 
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    
    # Create index if not exists
    op.execute("CREATE INDEX IF NOT EXISTS ix_chaser_requests_engagement_id ON chaser_requests(engagement_id)")
    
    # Drop vat_period_id from chaser_requests (if exists)
    try:
        op.drop_constraint('chaser_requests_vat_period_id_fkey', 'chaser_requests', type_='foreignkey')
    except Exception:
        pass  # Constraint may not exist
    op.execute("ALTER TABLE chaser_requests DROP COLUMN IF EXISTS vat_period_id")
    
    # Make engagement_id required (if possible)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE chaser_requests ALTER COLUMN engagement_id SET NOT NULL;
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)
    
    # Drop deprecated tables (IF EXISTS)
    op.execute('DROP TABLE IF EXISTS audit_trail_entries CASCADE')
    op.execute('DROP TABLE IF EXISTS checklist_items CASCADE')
    op.execute('DROP TABLE IF EXISTS evidence_items CASCADE')
    op.execute('DROP TABLE IF EXISTS vat_periods CASCADE')
    
    # Drop deprecated enums
    op.execute('DROP TYPE IF EXISTS periodstatus')
    op.execute('DROP TYPE IF EXISTS evidencestatus')
    op.execute('DROP TYPE IF EXISTS evidencecategory')
    op.execute('DROP TYPE IF EXISTS documenttype')


def downgrade() -> None:
    # Re-create deprecated enums
    periodstatus = postgresql.ENUM(
        'DRAFT', 'IN_PROGRESS', 'UNDER_REVIEW', 'READY', 'SUBMITTED', 'LOCKED',
        name='periodstatus'
    )
    periodstatus.create(op.get_bind(), checkfirst=True)
    
    evidencestatus = postgresql.ENUM(
        'PENDING', 'PARTIAL', 'COMPLETE', 'VALIDATED', 'EXCEPTION',
        name='evidencestatus'
    )
    evidencestatus.create(op.get_bind(), checkfirst=True)
    
    evidencecategory = postgresql.ENUM(
        'SALES_INVOICES', 'PURCHASE_INVOICES', 'CREDIT_NOTES', 'DEBIT_NOTES',
        'BANK_STATEMENTS', 'RECEIPTS', 'CONTRACTS', 'IMPORT_DOCUMENTS',
        'EXPORT_DOCUMENTS', 'VAT_CERTIFICATES', 'OTHER',
        name='evidencecategory'
    )
    evidencecategory.create(op.get_bind(), checkfirst=True)
    
    documenttype = postgresql.ENUM(
        'INVOICE', 'CREDIT_NOTE', 'DEBIT_NOTE', 'RECEIPT', 'BANK_STATEMENT',
        'CONTRACT', 'IMPORT_DECLARATION', 'EXPORT_DECLARATION', 'VAT_CERTIFICATE',
        'PAYROLL', 'OTHER',
        name='documenttype'
    )
    documenttype.create(op.get_bind(), checkfirst=True)
    
    # Re-create vat_periods table
    op.create_table('vat_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'IN_PROGRESS', 'UNDER_REVIEW', 'READY', 'SUBMITTED', 'LOCKED', name='periodstatus'), nullable=False),
        sa.Column('is_locked', sa.Boolean(), nullable=False),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Re-create evidence_items table
    op.create_table('evidence_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vat_period_id', sa.Integer(), nullable=False),
        sa.Column('category', postgresql.ENUM('SALES_INVOICES', 'PURCHASE_INVOICES', 'CREDIT_NOTES', 'DEBIT_NOTES', 'BANK_STATEMENTS', 'RECEIPTS', 'CONTRACTS', 'IMPORT_DOCUMENTS', 'EXPORT_DOCUMENTS', 'VAT_CERTIFICATES', 'OTHER', name='evidencecategory'), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'PARTIAL', 'COMPLETE', 'VALIDATED', 'EXCEPTION', name='evidencestatus'), nullable=False),
        sa.Column('expected_count', sa.Integer(), nullable=False),
        sa.Column('received_count', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vat_period_id'], ['vat_periods.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Re-create checklist_items table
    op.create_table('checklist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('acceptance', sa.String(50), nullable=False),
        sa.Column('cta_action', sa.String(50), nullable=False),
        sa.Column('cta_data', sa.String(2000), nullable=True),
        sa.Column('uploaded_file_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_checklist_items_client_id', 'checklist_items', ['client_id'])
    
    # Re-create audit_trail_entries table
    op.create_table('audit_trail_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vat_period_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('performed_by', sa.String(255), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('old_value', sa.String(2000), nullable=True),
        sa.Column('new_value', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vat_period_id'], ['vat_periods.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Restore chaser_requests vat_period_id
    op.add_column('chaser_requests', sa.Column('vat_period_id', sa.Integer(), nullable=True))
    op.create_foreign_key('chaser_requests_vat_period_id_fkey', 'chaser_requests', 'vat_periods',
                          ['vat_period_id'], ['id'])
    op.drop_constraint('fk_chaser_requests_engagement_id', 'chaser_requests', type_='foreignkey')
    op.drop_index('ix_chaser_requests_engagement_id', table_name='chaser_requests')
    op.drop_column('chaser_requests', 'engagement_id')
    
    # Restore legacy columns on documents
    op.add_column('documents', sa.Column('extracted_data', sa.JSON(), nullable=True))
    op.add_column('documents', sa.Column('document_type', postgresql.ENUM('INVOICE', 'CREDIT_NOTE', 'DEBIT_NOTE', 'RECEIPT', 'BANK_STATEMENT', 'CONTRACT', 'IMPORT_DECLARATION', 'EXPORT_DECLARATION', 'VAT_CERTIFICATE', 'PAYROLL', 'OTHER', name='documenttype'), nullable=True))
    op.add_column('documents', sa.Column('evidence_item_id', sa.Integer(), nullable=True))
    op.create_foreign_key('documents_evidence_item_id_fkey', 'documents', 'evidence_items',
                          ['evidence_item_id'], ['id'])
    
    # Make client_id nullable again
    op.alter_column('documents', 'client_id',
                    existing_type=sa.Integer(),
                    nullable=True)
