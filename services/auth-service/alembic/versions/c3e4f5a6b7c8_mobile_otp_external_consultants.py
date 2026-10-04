"""mobile OTP external consultant identity

Revision ID: c3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3e4f5a6b7c8"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("external_signup_challenges", "email_normalized", existing_type=sa.String(255), nullable=True)
    op.add_column("external_signup_challenges", sa.Column("mobile_normalized", sa.String(20), nullable=True))
    op.create_index("ix_external_signup_challenges_mobile", "external_signup_challenges", ["mobile_normalized"])
    op.execute("UPDATE external_signup_challenges SET status = 'OTP_PENDING' WHERE status = 'PENDING'")
    op.execute("UPDATE external_signup_challenges SET status = 'MOBILE_VERIFIED' WHERE status = 'VERIFIED'")
    op.execute("UPDATE external_signup_challenges SET status = 'OTP_EXPIRED' WHERE status = 'EXPIRED'")


def downgrade() -> None:
    op.execute("UPDATE external_signup_challenges SET status = 'PENDING' WHERE status = 'OTP_PENDING'")
    op.execute("UPDATE external_signup_challenges SET status = 'VERIFIED' WHERE status = 'MOBILE_VERIFIED'")
    op.execute("UPDATE external_signup_challenges SET status = 'EXPIRED' WHERE status = 'OTP_EXPIRED'")
    op.drop_index("ix_external_signup_challenges_mobile", table_name="external_signup_challenges")
    op.drop_column("external_signup_challenges", "mobile_normalized")
    op.execute("DELETE FROM external_signup_challenges WHERE email_normalized IS NULL")
    op.alter_column("external_signup_challenges", "email_normalized", existing_type=sa.String(255), nullable=False)
