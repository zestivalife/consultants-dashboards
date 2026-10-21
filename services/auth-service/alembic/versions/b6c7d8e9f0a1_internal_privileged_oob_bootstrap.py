"""Add audited out-of-band internal privileged enrolment metadata.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
"""
from alembic import op
import sqlalchemy as sa

revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("internal_privileged_invitations", sa.Column("delivery_channel", sa.String(32), nullable=False, server_default="EMAIL"))
    op.add_column("internal_privileged_invitations", sa.Column("administrative_identity_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("internal_privileged_invitations", sa.Column("administrative_identity_verified_by_user_id", sa.UUID(), nullable=True))
    op.add_column("internal_privileged_invitations", sa.Column("administrative_verification_reason", sa.String(500), nullable=True))
    op.create_foreign_key(
        "fk_internal_privileged_admin_verified_by",
        "internal_privileged_invitations",
        "users",
        ["administrative_identity_verified_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_internal_privileged_admin_verified_by", "internal_privileged_invitations", type_="foreignkey")
    op.drop_column("internal_privileged_invitations", "administrative_verification_reason")
    op.drop_column("internal_privileged_invitations", "administrative_identity_verified_by_user_id")
    op.drop_column("internal_privileged_invitations", "administrative_identity_verified_at")
    op.drop_column("internal_privileged_invitations", "delivery_channel")
