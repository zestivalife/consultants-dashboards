"""harden invitation tokens and add email outbox

Revision ID: f6a7b8c9d0e1
Revises: e4f6a7b8c9d0
Create Date: 2026-07-15 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e4f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.add_column("user_invitations", sa.Column("token_hash", sa.String(length=64), nullable=True))
    op.add_column("user_invitations", sa.Column("token_fingerprint", sa.String(length=16), nullable=True))
    op.add_column(
        "user_invitations",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.execute(
        """
        UPDATE user_invitations
        SET token_hash = encode(digest(token, 'sha256'), 'hex')
        WHERE token_hash IS NULL
        """
    )
    op.execute(
        """
        UPDATE user_invitations
        SET token_fingerprint = substring(token_hash from 1 for 12)
        WHERE token_fingerprint IS NULL
        """
    )
    op.execute(
        """
        UPDATE user_invitations
        SET token = 'redacted:' || id::text
        WHERE token NOT LIKE 'redacted:%'
        """
    )

    op.alter_column("user_invitations", "token_hash", nullable=False)
    op.create_unique_constraint("uq_user_invitations_token_hash", "user_invitations", ["token_hash"])
    op.create_index("ix_user_invitations_product_id", "user_invitations", ["product_id"], unique=False)
    op.create_index("ix_user_invitations_organization_id", "user_invitations", ["organization_id"], unique=False)
    op.create_index("ix_user_invitations_expires_at", "user_invitations", ["expires_at"], unique=False)

    op.create_table(
        "invitation_email_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("invitation_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="PENDING"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["invitation_id"], ["user_invitations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invitation_email_outbox_invitation_id", "invitation_email_outbox", ["invitation_id"])
    op.create_index("ix_invitation_email_outbox_email", "invitation_email_outbox", ["email"])
    op.create_index("ix_invitation_email_outbox_event_type", "invitation_email_outbox", ["event_type"])
    op.create_index("ix_invitation_email_outbox_status", "invitation_email_outbox", ["status"])


def downgrade() -> None:
    op.drop_index("ix_invitation_email_outbox_status", table_name="invitation_email_outbox")
    op.drop_index("ix_invitation_email_outbox_event_type", table_name="invitation_email_outbox")
    op.drop_index("ix_invitation_email_outbox_email", table_name="invitation_email_outbox")
    op.drop_index("ix_invitation_email_outbox_invitation_id", table_name="invitation_email_outbox")
    op.drop_table("invitation_email_outbox")

    op.drop_index("ix_user_invitations_expires_at", table_name="user_invitations")
    op.drop_index("ix_user_invitations_organization_id", table_name="user_invitations")
    op.drop_index("ix_user_invitations_product_id", table_name="user_invitations")
    op.drop_constraint("uq_user_invitations_token_hash", "user_invitations", type_="unique")
    op.drop_column("user_invitations", "updated_at")
    op.drop_column("user_invitations", "token_fingerprint")
    op.drop_column("user_invitations", "token_hash")
