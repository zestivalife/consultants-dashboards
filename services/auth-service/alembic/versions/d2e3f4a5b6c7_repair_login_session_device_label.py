"""repair login session device label

Revision ID: d2e3f4a5b6c7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-18 17:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(conn: sa.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(conn).get_table_names()


def _has_column(conn: sa.Connection, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in sa.inspect(conn).get_columns(table_name))


def upgrade() -> None:
    conn = op.get_bind()
    if _has_table(conn, "login_sessions") and not _has_column(conn, "login_sessions", "device_label"):
        op.add_column("login_sessions", sa.Column("device_label", sa.String(length=160), nullable=True))


def downgrade() -> None:
    # Preserve session metadata during rollback of this production schema repair.
    pass
