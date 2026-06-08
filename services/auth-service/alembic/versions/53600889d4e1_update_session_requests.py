"""update session requests

Revision ID: 53600889d4e1
Revises: 53600889d4e0
Create Date: 2026-04-07 20:51:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53600889d4e1'
down_revision: Union[str, None] = '53600889d4e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename columns
    op.alter_column('session_requests', 'preferred_date', new_column_name='scheduled_at')
    op.alter_column('session_requests', 'expected_participants', new_column_name='target_audience')
    
    # Add new columns
    op.add_column('session_requests', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('session_requests', sa.Column('mode', sa.String(50), server_default='ONLINE', nullable=False))
    op.add_column('session_requests', sa.Column('duration', sa.Integer(), server_default='60', nullable=False))
    op.add_column('session_requests', sa.Column('timezone', sa.String(50), server_default='Asia/Kolkata', nullable=False))
    op.add_column('session_requests', sa.Column('request_notes', sa.Text(), nullable=True))
    op.add_column('session_requests', sa.Column('team_id', sa.UUID(), sa.ForeignKey('teams.id'), nullable=True))

def downgrade() -> None:
    # Drop new columns
    op.drop_column('session_requests', 'team_id')
    op.drop_column('session_requests', 'request_notes')
    op.drop_column('session_requests', 'timezone')
    op.drop_column('session_requests', 'duration')
    op.drop_column('session_requests', 'mode')
    op.drop_column('session_requests', 'description')
    
    # Revert rename
    op.alter_column('session_requests', 'target_audience', new_column_name='expected_participants')
    op.alter_column('session_requests', 'scheduled_at', new_column_name='preferred_date')
