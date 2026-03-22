"""initial schema

Revision ID: 000000000000
Revises: 
Create Date: 2026-03-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000000000000'
down_revision = None
branch_labels = None
default_branch = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('display_name', sa.Text(), nullable=True),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("role IN ('regular', 'therapist', 'guardian')", name='chk_users_role'),
    )

    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_active', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
    )

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('sender', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('emotion_label', sa.Text(), nullable=True),
        sa.Column('emotion_score', sa.Float(), nullable=True),
        sa.Column('danger_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("sender IN ('user', 'assistant')", name='chk_messages_sender'),
    )

    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('invitee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('sender_id != invitee_id', name='chk_invitations_sender_invitee_diff'),
        sa.UniqueConstraint('sender_id', 'invitee_id', name='uq_invitations_sender_invitee'),
    )

    op.create_table(
        'emotion_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id'), nullable=False, unique=True),
        sa.Column('dominant_emotion', sa.Text(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('snapshot_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_table(
        'chatbot_guidelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('authored_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('response_tone', sa.Text(), nullable=True),
        sa.Column('coping_strategies', sa.Text(), nullable=True),
        sa.Column('behavioral_boundaries', sa.Text(), nullable=True),
        sa.Column('sensitive_topics', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_table(
        'dashboard_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('summary_date', sa.Date(), nullable=False),
        sa.Column('session_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_messages', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('avg_session_duration_mins', sa.Float(), nullable=True),
        sa.Column('avg_emotion_score', sa.Float(), nullable=True),
        sa.Column('dominant_emotion', sa.Text(), nullable=True),
        sa.Column('danger_event_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )

    op.create_table(
        'danger_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id'), nullable=False),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('danger_alerts')
    op.drop_table('dashboard_summary')
    op.drop_table('chatbot_guidelines')
    op.drop_table('emotion_snapshots')
    op.drop_table('invitations')
    op.drop_table('messages')
    op.drop_table('chat_sessions')
    op.drop_table('users')
