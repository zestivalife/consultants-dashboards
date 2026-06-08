"""scoring tables

Revision ID: 0001
Revises:
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "health_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bmi_score", sa.Float(), nullable=True),
        sa.Column("whr_score", sa.Float(), nullable=True),
        sa.Column("muscle_score", sa.Float(), nullable=True),
        sa.Column("stress_score", sa.Float(), nullable=True),
        sa.Column("lifestyle_score", sa.Float(), nullable=True),
        sa.Column("total_health_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_scores_user_id", "health_scores", ["user_id"])

    op.create_table(
        "physical_ease_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("interpretation", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_physical_ease_scores_user_id", "physical_ease_scores", ["user_id"])

    op.create_table(
        "active_performance_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("energy_balance", sa.Float(), nullable=True),
        sa.Column("body_support", sa.Float(), nullable=True),
        sa.Column("nourishment", sa.Float(), nullable=True),
        sa.Column("recovery", sa.Float(), nullable=True),
        sa.Column("active_performance_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_active_performance_scores_user_id", "active_performance_scores", ["user_id"])

    op.create_table(
        "medical_index_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vitamin_d", sa.Float(), nullable=True),
        sa.Column("hba1c", sa.Float(), nullable=True),
        sa.Column("thyroid", sa.Float(), nullable=True),
        sa.Column("b12", sa.Float(), nullable=True),
        sa.Column("lipid_profile", sa.Float(), nullable=True),
        sa.Column("ferritin", sa.Float(), nullable=True),
        sa.Column("hemoglobin", sa.Float(), nullable=True),
        sa.Column("crp", sa.Float(), nullable=True),
        sa.Column("medical_index", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medical_index_scores_user_id", "medical_index_scores", ["user_id"])


def downgrade() -> None:
    for table in ["medical_index_scores", "active_performance_scores", "physical_ease_scores", "health_scores"]:
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_table(table)
