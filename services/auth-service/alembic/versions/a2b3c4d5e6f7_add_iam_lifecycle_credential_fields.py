"""add iam lifecycle credential fields

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-26 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def _index_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {index["name"] for index in sa.inspect(conn).get_indexes(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    user_columns = _column_names(conn, "users")

    if "credential_status" not in user_columns:
        op.add_column(
            "users",
            sa.Column("credential_status", sa.String(length=40), nullable=False, server_default="PERMANENT"),
        )
        op.alter_column("users", "credential_status", server_default=None)

    if "temporary_password_created_at" not in user_columns:
        op.add_column("users", sa.Column("temporary_password_created_at", sa.DateTime(timezone=True), nullable=True))

    if "temporary_password_expires_at" not in user_columns:
        op.add_column("users", sa.Column("temporary_password_expires_at", sa.DateTime(timezone=True), nullable=True))

    if "temporary_password_consumed_at" not in user_columns:
        op.add_column("users", sa.Column("temporary_password_consumed_at", sa.DateTime(timezone=True), nullable=True))

    indexes = _index_names(conn, "users")
    if "ix_users_credential_status" not in indexes:
        op.create_index("ix_users_credential_status", "users", ["credential_status"])
    if "ix_users_temporary_password_expires_at" not in indexes:
        op.create_index("ix_users_temporary_password_expires_at", "users", ["temporary_password_expires_at"])

    conn.execute(
        sa.text(
            """
            UPDATE users
            SET credential_status = CASE
                WHEN must_change_password = true THEN 'TEMPORARY'
                ELSE 'PERMANENT'
            END
            WHERE credential_status IS NULL
               OR credential_status = 'PERMANENT'
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    indexes = _index_names(conn, "users")
    if "ix_users_temporary_password_expires_at" in indexes:
        op.drop_index("ix_users_temporary_password_expires_at", table_name="users")
    if "ix_users_credential_status" in indexes:
        op.drop_index("ix_users_credential_status", table_name="users")

    user_columns = _column_names(conn, "users")
    for column_name in (
        "temporary_password_consumed_at",
        "temporary_password_expires_at",
        "temporary_password_created_at",
        "credential_status",
    ):
        if column_name in user_columns:
            op.drop_column("users", column_name)
