"""external consultant signup authority

Revision ID: c2d3e4f5a6b7
Revises: c1e2f3a4b5c6
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "c1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "external_signup_challenges",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email_normalized", sa.String(255), nullable=False),
        sa.Column("otp_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resend_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_external_signup_challenges_email", "external_signup_challenges", ["email_normalized"])
    op.create_index("ix_external_signup_challenges_status", "external_signup_challenges", ["status"])
    op.create_table(
        "external_signup_provisioning",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("challenge_id", sa.UUID(), sa.ForeignKey("external_signup_challenges.id", ondelete="RESTRICT"), unique=True, nullable=False),
        sa.Column("auth_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False),
        sa.Column("account_type", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(180), unique=True, nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="AUTH_IDENTITY_LINKED"),
        sa.Column("fiteatsy_user_id", sa.String(180)),
        sa.Column("tenant_id", sa.String(80)),
        sa.Column("owner_membership_id", sa.String(80)),
        sa.Column("onboarding_id", sa.String(80)),
        sa.Column("last_error_code", sa.String(100)),
        sa.Column("last_error_detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("external_signup_provisioning")
    op.drop_index("ix_external_signup_challenges_status", table_name="external_signup_challenges")
    op.drop_index("ix_external_signup_challenges_email", table_name="external_signup_challenges")
    op.drop_table("external_signup_challenges")
