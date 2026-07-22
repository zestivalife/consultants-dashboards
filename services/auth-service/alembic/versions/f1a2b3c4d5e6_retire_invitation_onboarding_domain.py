"""retire invitation onboarding domain

Revision ID: f1a2b3c4d5e6
Revises: f0a1b2c3d4e5
Create Date: 2026-07-22 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names(conn: sa.Connection) -> set[str]:
    return set(sa.inspect(conn).get_table_names())


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    if table_name not in _table_names(conn):
        return set()
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    table_names = _table_names(conn)

    if {"role_permissions", "permissions"} <= table_names:
        conn.execute(
            sa.text(
                """
                DELETE FROM role_permissions
                USING permissions
                WHERE role_permissions.permission_id = permissions.id
                  AND permissions.key = 'users.invite'
                """
            )
        )

    if "permissions" in table_names:
        conn.execute(sa.text("DELETE FROM permissions WHERE key = 'users.invite'"))

    if "onboarding_instances" in table_names and "invitation_id" in _column_names(conn, "onboarding_instances"):
        op.drop_column("onboarding_instances", "invitation_id")

    if "invitation_email_outbox" in table_names:
        op.drop_table("invitation_email_outbox")

    if "user_invitations" in table_names:
        op.drop_table("user_invitations")

    if "otp_verifications" in table_names:
        op.drop_table("otp_verifications")


def downgrade() -> None:
    # Invitation-based onboarding has been retired by product architecture.
    # Recreating token or email-outbox tables on downgrade would reintroduce a
    # forbidden workflow, so rollback must restore a prior application release
    # from backup if this production decision ever changes.
    pass
