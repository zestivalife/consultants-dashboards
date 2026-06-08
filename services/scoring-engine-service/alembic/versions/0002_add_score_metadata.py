"""add score metadata columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "health_scores",
    "physical_ease_scores",
    "active_performance_scores",
    "medical_index_scores",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("score_version", sa.String(20), nullable=False, server_default="v1"))
        op.add_column(table, sa.Column("algorithm_version", sa.String(20), nullable=False, server_default="2026-03"))
        op.add_column(table, sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "computed_at")
        op.drop_column(table, "algorithm_version")
        op.drop_column(table, "score_version")
