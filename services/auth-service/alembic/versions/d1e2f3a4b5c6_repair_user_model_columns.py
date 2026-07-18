"""repair user model columns

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-07-18 16:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OPTIONAL_USER_COLUMNS = [
    ("company_name", sa.Column("company_name", sa.String(length=255), nullable=True)),
    ("location", sa.Column("location", sa.String(length=255), nullable=True)),
    ("employees", sa.Column("employees", sa.Integer(), nullable=True)),
    ("industry", sa.Column("industry", sa.String(length=255), nullable=True)),
    ("company_id", sa.Column("company_id", sa.Uuid(), nullable=True)),
    ("first_name", sa.Column("first_name", sa.String(length=100), nullable=True)),
    ("last_name", sa.Column("last_name", sa.String(length=100), nullable=True)),
    ("phone", sa.Column("phone", sa.String(length=20), nullable=True)),
    ("avatar_url", sa.Column("avatar_url", sa.String(length=500), nullable=True)),
    ("last_login_at", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True)),
    ("deleted_at", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)),
]

REQUIRED_USER_COLUMNS = [
    (
        "is_active",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        "true",
        sa.Boolean(),
    ),
    (
        "status",
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
        "'ACTIVE'",
        sa.String(length=40),
    ),
    (
        "permissions",
        sa.Column("permissions", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        "'[]'::json",
        sa.JSON(),
    ),
]


def _column_names(conn: sa.Connection) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns("users")}


def _index_names(conn: sa.Connection) -> set[str]:
    return {index["name"] for index in sa.inspect(conn).get_indexes("users")}


def _has_company_fk(conn: sa.Connection) -> bool:
    for foreign_key in sa.inspect(conn).get_foreign_keys("users"):
        if foreign_key.get("constrained_columns") == ["company_id"]:
            return True
    return False


def upgrade() -> None:
    conn = op.get_bind()
    existing_columns = _column_names(conn)

    for column_name, column in OPTIONAL_USER_COLUMNS:
        if column_name not in existing_columns:
            op.add_column("users", column)

    existing_columns = _column_names(conn)
    for column_name, column, fallback_sql, _existing_type in REQUIRED_USER_COLUMNS:
        if column_name not in existing_columns:
            op.add_column("users", column)
        else:
            conn.execute(sa.text(f"UPDATE users SET {column_name} = {fallback_sql} WHERE {column_name} IS NULL"))

    for column_name, _, _, existing_type in REQUIRED_USER_COLUMNS:
        op.alter_column(
            "users",
            column_name,
            existing_type=existing_type,
            nullable=False,
            server_default=None,
        )

    if "company_id" in _column_names(conn) and not _has_company_fk(conn):
        op.create_foreign_key(
            "fk_users_company_id_users",
            "users",
            "users",
            ["company_id"],
            ["id"],
        )

    existing_indexes = _index_names(conn)
    if "ix_users_status" not in existing_indexes:
        op.create_index("ix_users_status", "users", ["status"], unique=False)


def downgrade() -> None:
    # This repair migration synchronizes drifted production schemas with the
    # canonical User ORM. Downgrade is intentionally non-destructive.
    pass
