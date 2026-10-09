"""Governed in-house QA identity classification and provisioning ledger."""

from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("account_classification", sa.String(40), nullable=False, server_default="PRODUCTION_USER"))
    op.create_check_constraint(
        "ck_users_account_classification",
        "users",
        "account_classification in ('PRODUCTION_USER','GOVERNED_QA_INHOUSE')",
    )
    op.create_index("ix_users_account_classification", "users", ["account_classification"])
    op.create_table(
        "inhouse_qa_provisioning",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fixture_key", sa.String(96), nullable=False, unique=True),
        sa.Column("auth_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("fiteatsy_user_id", sa.String(180), nullable=True, unique=True),
        sa.Column("canonical_role", sa.String(40), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("last_error_code", sa.String(80), nullable=True),
        sa.Column("created_by_reference", sa.String(180), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status in ('PENDING','READY','COMPENSATED','FAILED')", name="ck_inhouse_qa_provisioning_status"),
        sa.CheckConstraint("canonical_role in ('user','consultant','provider','dietician','senior_consultant','practitioner','mentor','admin','super_admin','platform_owner')", name="ck_inhouse_qa_provisioning_role"),
    )


def downgrade() -> None:
    op.drop_table("inhouse_qa_provisioning")
    op.drop_index("ix_users_account_classification", table_name="users")
    op.drop_constraint("ck_users_account_classification", "users", type_="check")
    op.drop_column("users", "account_classification")
