"""add people access archive metadata

Revision ID: f3a4b5c6d7e8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-02 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    columns = _column_names(conn, "users")

    if "archived_at" not in columns:
        op.add_column("users", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_users_archived_at", "users", ["archived_at"])

    if "archived_by_user_id" not in columns:
        op.add_column("users", sa.Column("archived_by_user_id", sa.UUID(), nullable=True))
        op.create_foreign_key(
            "fk_users_archived_by_user_id_users",
            "users",
            "users",
            ["archived_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if "archive_reason" not in columns:
        op.add_column("users", sa.Column("archive_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    columns = _column_names(conn, "users")

    if "archive_reason" in columns:
        op.drop_column("users", "archive_reason")

    if "archived_by_user_id" in columns:
        op.drop_constraint("fk_users_archived_by_user_id_users", "users", type_="foreignkey")
        op.drop_column("users", "archived_by_user_id")

    if "archived_at" in columns:
        op.drop_index("ix_users_archived_at", table_name="users")
        op.drop_column("users", "archived_at")
