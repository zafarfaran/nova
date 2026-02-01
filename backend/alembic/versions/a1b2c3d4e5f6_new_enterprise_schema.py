"""New enterprise schema migration

Revision ID: a1b2c3d4e5f6
Revises: 4c9a8a1d2f5e
Create Date: 2026-02-01 12:00:00.000000

This migration adds the new enterprise schema tables while preserving
backwards compatibility with existing tables. Key additions:
- ClientContact for multiple contacts per client
- Engagement to replace VATPeriod with generic engagements
- DocumentCategory and DocumentType for configurable document types
- FileObject for storage metadata
- DocumentVersion for version tracking and AI extraction results
- Counterparty for supplier/customer tracking
- FinancialAccount to replace BankConnection
- RequestSet and RequestItem to replace EvidenceItem and ChecklistItem
- RequestTemplate for reusable request patterns
- AuditLog for unified audit trail

Also adds new columns to existing tables:
- Client: client_type, display_name, country_code, company_number, utr, ni_number, vat_registered
- Document: client_id, engagement_id, document_type_id, counterparty_id, account_id, title, source, document_date, period_start, period_end, meta
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4c9a8a1d2f5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums for new tables using raw SQL (safer with checkfirst logic)
    op.execute("DO $$ BEGIN CREATE TYPE engagementtype AS ENUM ('vat_return', 'annual_accounts', 'tax_return', 'audit', 'bookkeeping', 'other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE engagementstatus AS ENUM ('draft', 'in_progress', 'under_review', 'ready', 'submitted', 'locked'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE counterpartytype AS ENUM ('supplier', 'customer', 'both'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE accounttype AS ENUM ('bank_current', 'bank_savings', 'credit_card', 'payment_processor', 'merchant', 'other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE requestsetstatus AS ENUM ('draft', 'sent', 'partial', 'complete', 'expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE requestitemstatus AS ENUM ('pending', 'partial', 'complete', 'waived'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE extractionstatus AS ENUM ('pending', 'processing', 'extracted', 'failed'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    
    # Define enum types for column references (create_type=False prevents SQLAlchemy from creating them again)
    engagement_type = postgresql.ENUM('vat_return', 'annual_accounts', 'tax_return', 'audit', 'bookkeeping', 'other', name='engagementtype', create_type=False)
    engagement_status = postgresql.ENUM('draft', 'in_progress', 'under_review', 'ready', 'submitted', 'locked', name='engagementstatus', create_type=False)
    counterparty_type = postgresql.ENUM('supplier', 'customer', 'both', name='counterpartytype', create_type=False)
    account_type = postgresql.ENUM('bank_current', 'bank_savings', 'credit_card', 'payment_processor', 'merchant', 'other', name='accounttype', create_type=False)
    request_set_status = postgresql.ENUM('draft', 'sent', 'partial', 'complete', 'expired', name='requestsetstatus', create_type=False)
    request_item_status = postgresql.ENUM('pending', 'partial', 'complete', 'waived', name='requestitemstatus', create_type=False)
    extraction_status = postgresql.ENUM('pending', 'processing', 'extracted', 'failed', name='extractionstatus', create_type=False)
    
    # Add new columns to clients table
    op.add_column('clients', sa.Column('client_type', sa.String(50), nullable=True))
    op.add_column('clients', sa.Column('display_name', sa.String(255), nullable=True))
    op.add_column('clients', sa.Column('country_code', sa.String(2), server_default='GB', nullable=False))
    op.add_column('clients', sa.Column('company_number', sa.String(20), nullable=True))
    op.add_column('clients', sa.Column('utr', sa.String(20), nullable=True))
    op.add_column('clients', sa.Column('ni_number', sa.String(20), nullable=True))
    op.add_column('clients', sa.Column('vat_registered', sa.Boolean(), server_default='false', nullable=False))
    
    # Create client_contacts table
    op.create_table('client_contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_client_contacts_client_id', 'client_contacts', ['client_id'])
    
    # Create engagements table - use the enum variables directly
    op.create_table('engagements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('engagement_type', engagement_type, nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('status', engagement_status, server_default='draft', nullable=False),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.Column('is_locked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_engagements_client_id', 'engagements', ['client_id'])
    
    # Create document_categories table
    op.create_table('document_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create document_types table
    op.create_table('document_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('client_type_scope', sa.String(50), nullable=True),
        sa.Column('requires_counterparty', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_account', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_engagement', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('retention_years', sa.Integer(), server_default='7', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['document_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_document_types_category_id', 'document_types', ['category_id'])
    
    # Create counterparties table
    op.create_table('counterparties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('counterparty_type', counterparty_type, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('vat_number', sa.String(20), nullable=True),
        sa.Column('external_ref', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_counterparties_client_id', 'counterparties', ['client_id'])
    
    # Create financial_accounts table
    op.create_table('financial_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('account_type', account_type, nullable=False),
        sa.Column('provider', sa.String(255), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('currency_code', sa.String(3), server_default='GBP', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('plaid_access_token', sa.String(255), nullable=True),
        sa.Column('plaid_item_id', sa.String(100), nullable=True),
        sa.Column('account_id', sa.String(100), nullable=True),
        sa.Column('account_mask', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_financial_accounts_client_id', 'financial_accounts', ['client_id'])
    
    # Create file_objects table
    op.create_table('file_objects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('storage_provider', sa.String(50), nullable=False),
        sa.Column('bucket', sa.String(255), nullable=False),
        sa.Column('object_key', sa.String(1000), nullable=False),
        sa.Column('byte_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('checksum_sha256', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('object_key')
    )
    op.create_index('ix_file_objects_checksum_sha256', 'file_objects', ['checksum_sha256'])
    
    # Add new columns to documents table
    op.add_column('documents', sa.Column('client_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('engagement_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('document_type_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('counterparty_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('account_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('title', sa.String(255), nullable=True))
    op.add_column('documents', sa.Column('source', sa.String(50), server_default='upload', nullable=False))
    op.add_column('documents', sa.Column('document_date', sa.Date(), nullable=True))
    op.add_column('documents', sa.Column('period_start', sa.Date(), nullable=True))
    op.add_column('documents', sa.Column('period_end', sa.Date(), nullable=True))
    op.add_column('documents', sa.Column('meta', sa.JSON(), nullable=True))
    
    # Create foreign key constraints for documents
    op.create_foreign_key('fk_documents_client_id', 'documents', 'clients', ['client_id'], ['id'])
    op.create_foreign_key('fk_documents_engagement_id', 'documents', 'engagements', ['engagement_id'], ['id'])
    op.create_foreign_key('fk_documents_document_type_id', 'documents', 'document_types', ['document_type_id'], ['id'])
    op.create_foreign_key('fk_documents_counterparty_id', 'documents', 'counterparties', ['counterparty_id'], ['id'])
    op.create_foreign_key('fk_documents_account_id', 'documents', 'financial_accounts', ['account_id'], ['id'])
    
    # Create indexes for documents
    op.create_index('ix_documents_client_id', 'documents', ['client_id'])
    op.create_index('ix_documents_engagement_id', 'documents', ['engagement_id'])
    op.create_index('ix_documents_document_type_id', 'documents', ['document_type_id'])
    op.create_index('ix_documents_counterparty_id', 'documents', ['counterparty_id'])
    op.create_index('ix_documents_account_id', 'documents', ['account_id'])
    
    # Create document_versions table
    op.create_table('document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('file_object_id', sa.Integer(), nullable=False),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=False),
        sa.Column('uploaded_by_contact_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('extraction_status', extraction_status, server_default='pending', nullable=False),
        sa.Column('processing_error', sa.String(2000), nullable=True),
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_object_id'], ['file_objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_contact_id'], ['client_contacts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'version_no', name='uq_document_versions_document_version')
    )
    op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'])
    op.create_index('ix_document_versions_file_object_id', 'document_versions', ['file_object_id'])
    
    # Create request_sets table
    op.create_table('request_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('engagement_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', request_set_status, server_default='draft', nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('upload_token', sa.String(64), nullable=True),
        sa.Column('sent_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('upload_token')
    )
    op.create_index('ix_request_sets_engagement_id', 'request_sets', ['engagement_id'])
    
    # Create request_items table
    op.create_table('request_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_set_id', sa.Integer(), nullable=False),
        sa.Column('document_type_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('expected_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('status', request_item_status, server_default='pending', nullable=False),
        sa.Column('assigned_to_contact_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['request_set_id'], ['request_sets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to_contact_id'], ['client_contacts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_request_items_request_set_id', 'request_items', ['request_set_id'])
    op.create_index('ix_request_items_document_type_id', 'request_items', ['document_type_id'])
    
    # Create request_item_documents junction table
    op.create_table('request_item_documents',
        sa.Column('request_item_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['request_item_id'], ['request_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('request_item_id', 'document_id')
    )
    
    # Create request_templates table
    op.create_table('request_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('client_type', sa.String(50), nullable=True),
        sa.Column('engagement_type', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create request_template_items table
    op.create_table('request_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('document_type_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('expected_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('order_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['request_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_request_template_items_template_id', 'request_template_items', ['template_id'])
    op.create_index('ix_request_template_items_document_type_id', 'request_template_items', ['document_type_id'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('engagement_id', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('actor_contact_id', sa.Integer(), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_contact_id'], ['client_contacts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_client_id', 'audit_logs', ['client_id'])
    op.create_index('ix_audit_logs_engagement_id', 'audit_logs', ['engagement_id'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])


def downgrade() -> None:
    # Drop new tables in reverse order
    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_engagement_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_client_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('ix_request_template_items_document_type_id', table_name='request_template_items')
    op.drop_index('ix_request_template_items_template_id', table_name='request_template_items')
    op.drop_table('request_template_items')
    op.drop_table('request_templates')
    
    op.drop_table('request_item_documents')
    
    op.drop_index('ix_request_items_document_type_id', table_name='request_items')
    op.drop_index('ix_request_items_request_set_id', table_name='request_items')
    op.drop_table('request_items')
    
    op.drop_index('ix_request_sets_engagement_id', table_name='request_sets')
    op.drop_table('request_sets')
    
    op.drop_index('ix_document_versions_file_object_id', table_name='document_versions')
    op.drop_index('ix_document_versions_document_id', table_name='document_versions')
    op.drop_table('document_versions')
    
    # Drop new columns from documents
    op.drop_index('ix_documents_account_id', table_name='documents')
    op.drop_index('ix_documents_counterparty_id', table_name='documents')
    op.drop_index('ix_documents_document_type_id', table_name='documents')
    op.drop_index('ix_documents_engagement_id', table_name='documents')
    op.drop_index('ix_documents_client_id', table_name='documents')
    
    op.drop_constraint('fk_documents_account_id', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_counterparty_id', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_document_type_id', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_engagement_id', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_client_id', 'documents', type_='foreignkey')
    
    op.drop_column('documents', 'meta')
    op.drop_column('documents', 'period_end')
    op.drop_column('documents', 'period_start')
    op.drop_column('documents', 'document_date')
    op.drop_column('documents', 'source')
    op.drop_column('documents', 'title')
    op.drop_column('documents', 'account_id')
    op.drop_column('documents', 'counterparty_id')
    op.drop_column('documents', 'document_type_id')
    op.drop_column('documents', 'engagement_id')
    op.drop_column('documents', 'client_id')
    
    op.drop_index('ix_file_objects_checksum_sha256', table_name='file_objects')
    op.drop_table('file_objects')
    
    op.drop_index('ix_financial_accounts_client_id', table_name='financial_accounts')
    op.drop_table('financial_accounts')
    
    op.drop_index('ix_counterparties_client_id', table_name='counterparties')
    op.drop_table('counterparties')
    
    op.drop_index('ix_document_types_category_id', table_name='document_types')
    op.drop_table('document_types')
    op.drop_table('document_categories')
    
    op.drop_index('ix_engagements_client_id', table_name='engagements')
    op.drop_table('engagements')
    
    op.drop_index('ix_client_contacts_client_id', table_name='client_contacts')
    op.drop_table('client_contacts')
    
    # Drop new columns from clients
    op.drop_column('clients', 'vat_registered')
    op.drop_column('clients', 'ni_number')
    op.drop_column('clients', 'utr')
    op.drop_column('clients', 'company_number')
    op.drop_column('clients', 'country_code')
    op.drop_column('clients', 'display_name')
    op.drop_column('clients', 'client_type')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS extractionstatus')
    op.execute('DROP TYPE IF EXISTS requestitemstatus')
    op.execute('DROP TYPE IF EXISTS requestsetstatus')
    op.execute('DROP TYPE IF EXISTS accounttype')
    op.execute('DROP TYPE IF EXISTS counterpartytype')
    op.execute('DROP TYPE IF EXISTS engagementstatus')
    op.execute('DROP TYPE IF EXISTS engagementtype')
