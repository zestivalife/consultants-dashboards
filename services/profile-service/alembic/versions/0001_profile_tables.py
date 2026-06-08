"""profile tables: user_profiles, body_measurements, biomarkers, lifestyle_baseline

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
        "user_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("sex", sa.String(20), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("body_fat_percent", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)

    op.create_table(
        "body_measurements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("arm_circumference", sa.Float(), nullable=True),
        sa.Column("thigh_circumference", sa.Float(), nullable=True),
        sa.Column("calf_circumference", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_body_measurements_user_id", "body_measurements", ["user_id"], unique=True)

    op.create_table(
        "biomarkers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vitamin_d", sa.Float(), nullable=True),
        sa.Column("hba1c", sa.Float(), nullable=True),
        sa.Column("tsh", sa.Float(), nullable=True),
        sa.Column("b12", sa.Float(), nullable=True),
        sa.Column("hdl", sa.Float(), nullable=True),
        sa.Column("ldl", sa.Float(), nullable=True),
        sa.Column("triglycerides", sa.Float(), nullable=True),
        sa.Column("ferritin", sa.Float(), nullable=True),
        sa.Column("hemoglobin", sa.Float(), nullable=True),
        sa.Column("crp", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_biomarkers_user_id", "biomarkers", ["user_id"], unique=True)

    op.create_table(
        "lifestyle_baseline",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activity_level", sa.String(50), nullable=True),
        sa.Column("exercise_frequency", sa.Integer(), nullable=True),
        sa.Column("daily_steps", sa.Integer(), nullable=True),
        sa.Column("sleep_duration", sa.Float(), nullable=True),
        sa.Column("water_intake", sa.Float(), nullable=True),
        sa.Column("food_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lifestyle_baseline_user_id", "lifestyle_baseline", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_lifestyle_baseline_user_id", table_name="lifestyle_baseline")
    op.drop_table("lifestyle_baseline")
    op.drop_index("ix_biomarkers_user_id", table_name="biomarkers")
    op.drop_table("biomarkers")
    op.drop_index("ix_body_measurements_user_id", table_name="body_measurements")
    op.drop_table("body_measurements")
    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")
