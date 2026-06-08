"""normalize version defaults for old records

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
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
        op.execute(
            sa.text(
                f"UPDATE {table} SET score_version = 'v1' WHERE score_version = '1.0'"
            )
        )
        op.execute(
            sa.text(
                f"UPDATE {table} SET algorithm_version = '2026-03' WHERE algorithm_version = 'v1'"
            )
        )

        op.alter_column(table, "score_version", server_default="v1")
        op.alter_column(table, "algorithm_version", server_default="2026-03")


def downgrade() -> None:
    for table in TABLES:
        op.alter_column(table, "score_version", server_default="1.0")
        op.alter_column(table, "algorithm_version", server_default="v1")

        op.execute(
            sa.text(
                f"UPDATE {table} SET score_version = '1.0' WHERE score_version = 'v1'"
            )
        )
        op.execute(
            sa.text(
                f"UPDATE {table} SET algorithm_version = 'v1' WHERE algorithm_version = '2026-03'"
            )
        )
