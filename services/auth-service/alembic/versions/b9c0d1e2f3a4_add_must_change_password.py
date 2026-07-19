"""add must change password flag

Revision ID: b9c0d1e2f3a4
Revises: a7b8c9d0e1f2
Create Date: 2026-07-18 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9c0d1e2f3a4"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    if "must_change_password" not in _column_names(conn, "users"):
        op.add_column(
            "users",
            sa.Column(
                "must_change_password",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    op.alter_column("users", "must_change_password", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    if "must_change_password" in _column_names(conn, "users"):
        op.drop_column("users", "must_change_password")
