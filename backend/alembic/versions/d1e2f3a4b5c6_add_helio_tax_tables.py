"""Add Helio tax planning tables

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-02-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tax_profiles ---
    op.create_table('tax_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('tax_year', sa.String(), nullable=False),
        # Cached summary
        sa.Column('total_income', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('adjusted_net_income', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('taxable_income', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('income_tax', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('national_insurance', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('dividend_tax', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('total_tax', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('effective_rate', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('marginal_rate', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('personal_allowance', sa.Float(), server_default='12570.0', nullable=True),
        sa.Column('pa_status', sa.String(), server_default='full', nullable=True),
        # Flags
        sa.Column('in_pa_taper_zone', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('hicbc_applies', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('pension_taper_applies', sa.Boolean(), server_default='false', nullable=True),
        # JSON fields
        sa.Column('tax_breakdown', sa.JSON(), nullable=True),
        sa.Column('ni_breakdown', sa.JSON(), nullable=True),
        sa.Column('income_sources', sa.JSON(), nullable=True),
        sa.Column('pension_data', sa.JSON(), nullable=True),
        sa.Column('allowances', sa.JSON(), nullable=True),
        sa.Column('hicbc', sa.JSON(), nullable=True),
        sa.Column('scenarios', sa.JSON(), nullable=True),
        # Meta
        sa.Column('status', sa.String(), server_default='draft', nullable=True),
        sa.Column('data_confidence', sa.String(), server_default='low', nullable=True),
        sa.Column('confidence_notes', sa.JSON(), nullable=True),
        sa.Column('source_notes', sa.JSON(), nullable=True),
        # Timestamps from TimestampMixin
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'tax_year'),
    )

    # --- tax_observations ---
    op.create_table('tax_observations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('tax_year', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('priority', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('potential_saving', sa.Float(), nullable=True),
        sa.Column('deadline', sa.String(), nullable=True),
        sa.Column('action_required', sa.String(), nullable=True),
        sa.Column('is_dismissed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('source', sa.String(), server_default='engine', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- tax_meeting_notes ---
    op.create_table('tax_meeting_notes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.String(), nullable=True),
        sa.Column('meeting_date', sa.DateTime(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('attendees', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('action_items', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- tax_conversations ---
    op.create_table('tax_conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='active', nullable=True),
        sa.Column('last_message_preview', sa.String(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('message_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('unread', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('tax_plan_mode', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- tax_messages ---
    op.create_table('tax_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('insights', sa.JSON(), nullable=True),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('dashboard_data', sa.JSON(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['tax_conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- tax_context_snippets ---
    op.create_table('tax_context_snippets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('source_title', sa.String(), server_default='', nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('cleaned_markdown', sa.Text(), server_default='', nullable=False),
        sa.Column('capture_type', sa.String(), server_default='full_page', nullable=False),
        sa.Column('status', sa.String(), server_default='processing', nullable=False),
        sa.Column('is_consumed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Indexes for common queries
    op.create_index('ix_tax_profiles_client_id', 'tax_profiles', ['client_id'])
    op.create_index('ix_tax_observations_client_id', 'tax_observations', ['client_id'])
    op.create_index('ix_tax_meeting_notes_client_id', 'tax_meeting_notes', ['client_id'])
    op.create_index('ix_tax_conversations_client_id', 'tax_conversations', ['client_id'])
    op.create_index('ix_tax_messages_conversation_id', 'tax_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_tax_messages_conversation_id', table_name='tax_messages')
    op.drop_index('ix_tax_conversations_client_id', table_name='tax_conversations')
    op.drop_index('ix_tax_meeting_notes_client_id', table_name='tax_meeting_notes')
    op.drop_index('ix_tax_observations_client_id', table_name='tax_observations')
    op.drop_index('ix_tax_profiles_client_id', table_name='tax_profiles')

    # Drop in reverse dependency order (messages before conversations)
    op.drop_table('tax_context_snippets')
    op.drop_table('tax_messages')
    op.drop_table('tax_conversations')
    op.drop_table('tax_meeting_notes')
    op.drop_table('tax_observations')
    op.drop_table('tax_profiles')
