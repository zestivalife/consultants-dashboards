"""change target_audience from int to str

Revision ID: 53600889d4e3
Revises: 53600889d4e2
Create Date: 2026-04-13 00:00:00

Fix: target_audience was stored as an integer (inherited from expected_participants)
but the frontend and application layer expect string values like 'ALL_EMPLOYEES' or 'SPECIFIC_TEAM'.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '53600889d4e3'
down_revision: Union[str, None] = '53600889d4e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'session_requests',
        'target_audience',
        existing_type=sa.Integer(),
        type_=sa.String(50),
        existing_nullable=False,
        postgresql_using="CASE WHEN target_audience = 0 THEN 'ALL_EMPLOYEES' ELSE 'SPECIFIC_TEAM' END",
    )
    op.execute(
        "UPDATE session_requests SET target_audience = 'ALL_EMPLOYEES' WHERE target_audience IS NULL OR target_audience = '0'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE session_requests SET target_audience = '0'"
    )
    op.alter_column(
        'session_requests',
        'target_audience',
        existing_type=sa.String(50),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="0",
    )
