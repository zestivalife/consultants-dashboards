"""add team member system: memberships, notifications, metrics, user profile fields

Revision ID: 53600889d4e4
Revises: 53600889d4e3
Create Date: 2026-04-13 00:00:00

Adds:
- users.first_name, last_name, phone
- teams.join_code
- team_memberships table
- notifications table
- wellness_metrics table
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
import uuid


revision: str = '53600889d4e4'
down_revision: Union[str, None] = '53600889d4e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users: add profile fields ---
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'first_name' not in columns:
        op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    if 'last_name' not in columns:
        op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))
    if 'phone' not in columns:
        op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

    # --- teams: add join_code ---
    op.add_column('teams', sa.Column('join_code', sa.String(10), nullable=True))
    # Generate unique join codes for existing teams
    op.execute("""
        UPDATE teams
        SET join_code = UPPER(SUBSTRING(MD5(RANDOM()::TEXT), 1, 8))
        WHERE join_code IS NULL
    """)
    op.alter_column('teams', 'join_code', nullable=False)
    op.create_unique_constraint('uq_teams_join_code', 'teams', ['join_code'])
    op.create_index('ix_teams_join_code', 'teams', ['join_code'])

    # --- team_memberships table ---
    op.create_table(
        'team_memberships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('team_id', sa.UUID(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_lead', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id', name='uq_team_membership'),
    )
    op.create_index('ix_team_memberships_team_id', 'team_memberships', ['team_id'])
    op.create_index('ix_team_memberships_user_id', 'team_memberships', ['user_id'])

    # Back-fill: enrol existing team leads as members
    op.execute("""
        INSERT INTO team_memberships (id, team_id, user_id, is_lead, joined_at)
        SELECT gen_random_uuid(), id, lead_id, true, created_at
        FROM teams
        WHERE lead_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # --- notifications table ---
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False, server_default='system'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='low'),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])

    # --- wellness_metrics table ---
    op.create_table(
        'wellness_metrics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wellness_metrics_user_id', 'wellness_metrics', ['user_id'])
    op.create_index('ix_wellness_metrics_recorded_at', 'wellness_metrics', ['recorded_at'])


def downgrade() -> None:
    op.drop_table('wellness_metrics')
    op.drop_table('notifications')
    op.drop_table('team_memberships')
    op.drop_index('ix_teams_join_code', 'teams')
    op.drop_constraint('uq_teams_join_code', 'teams', type_='unique')
    op.drop_column('teams', 'join_code')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
