"""add corporate management

Revision ID: 53600889d4d9
Revises: 53600889d4d8
Create Date: 2026-03-29 18:08:03.229601

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '53600889d4d9'
down_revision: Union[str, None] = '53600889d4d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add company_id to users
    op.add_column('users', sa.Column('company_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True))

    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('lead_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create session_requests table
    op.create_table(
        'session_requests',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('preferred_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), server_default='SCHEDULED', nullable=False),
        sa.Column('expected_participants', sa.Integer(), server_default='0', nullable=False),
        sa.Column('company_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('session_requests')
    op.drop_table('teams')
    op.drop_column('users', 'company_id')
