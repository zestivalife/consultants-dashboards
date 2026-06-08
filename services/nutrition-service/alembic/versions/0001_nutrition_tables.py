"""nutrition tables

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
        "diet_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("calorie_target", sa.Float(), nullable=True),
        sa.Column("protein_target", sa.Float(), nullable=True),
        sa.Column("fat_target", sa.Float(), nullable=True),
        sa.Column("carb_target", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "meal_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("diet_plan_id", sa.Uuid(), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("meal_name", sa.String(200), nullable=False),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("protein", sa.Float(), nullable=True),
        sa.Column("carbs", sa.Float(), nullable=True),
        sa.Column("fats", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["diet_plan_id"], ["diet_plans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_meal_templates_diet_plan_id", "meal_templates", ["diet_plan_id"])

    op.create_table(
        "user_diet_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("diet_plan_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by", sa.Uuid(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["diet_plan_id"], ["diet_plans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_diet_plans_user_id", "user_diet_plans", ["user_id"])

    op.create_table(
        "health_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_reports_user_id", "health_reports", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_health_reports_user_id", table_name="health_reports")
    op.drop_table("health_reports")
    op.drop_index("ix_user_diet_plans_user_id", table_name="user_diet_plans")
    op.drop_table("user_diet_plans")
    op.drop_index("ix_meal_templates_diet_plan_id", table_name="meal_templates")
    op.drop_table("meal_templates")
    op.drop_table("diet_plans")
