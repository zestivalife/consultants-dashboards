"""add nutrition_baseline, user_goals tables and lifestyle columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to lifestyle_baseline
    op.add_column(
        "lifestyle_baseline",
        sa.Column("sleep_consistency", sa.Integer(), nullable=True),
    )
    op.add_column(
        "lifestyle_baseline",
        sa.Column("stress_level", sa.Integer(), nullable=True),
    )

    # Create nutrition_baseline table
    op.create_table(
        "nutrition_baseline",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("meal_frequency", sa.Integer(), nullable=True),
        sa.Column("protein_intake", sa.String(50), nullable=True),
        sa.Column("water_intake", sa.Float(), nullable=True),
        sa.Column("food_source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_nutrition_baseline_user_id",
        "nutrition_baseline",
        ["user_id"],
        unique=True,
    )

    # Create user_goals table
    op.create_table(
        "user_goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("goal_type", sa.String(50), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_goals_user_id",
        "user_goals",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_goals_user_id", table_name="user_goals")
    op.drop_table("user_goals")
    op.drop_index("ix_nutrition_baseline_user_id", table_name="nutrition_baseline")
    op.drop_table("nutrition_baseline")
    op.drop_column("lifestyle_baseline", "stress_level")
    op.drop_column("lifestyle_baseline", "sleep_consistency")
