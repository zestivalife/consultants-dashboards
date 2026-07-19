"""enforce platform owner lifecycle invariants

Revision ID: f0a1b2c3d4e5
Revises: e5f6a7b8c9d1
Create Date: 2026-07-19 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, None] = "e5f6a7b8c9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def _table_names(conn: sa.Connection) -> set[str]:
    return set(sa.inspect(conn).get_table_names())


def upgrade() -> None:
    conn = op.get_bind()
    users_columns = _column_names(conn, "users")
    table_names = _table_names(conn)

    assignments = [
        "is_active = true",
        "is_verified = true",
        "failed_login_attempts = 0",
        "lock_until = NULL",
        "updated_at = now()",
    ]
    if "email_verified" in users_columns:
        assignments.append("email_verified = true")
    if "status" in users_columns:
        assignments.append("status = 'ACTIVE'")
    if "must_change_password" in users_columns:
        assignments.append("must_change_password = false")
    if "deleted_at" in users_columns:
        assignments.append("deleted_at = NULL")

    role_filter = """
        EXISTS (
            SELECT 1
            FROM roles r
            WHERE r.id = users.role_id
              AND lower(r.name) IN ('platform_owner', 'superuser')
        )
    """
    if "user_roles" in table_names:
        role_filter = f"""
            ({role_filter})
            OR EXISTS (
                SELECT 1
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = users.id
                  AND lower(r.name) IN ('platform_owner', 'superuser')
            )
        """

    conn.execute(
        sa.text(
            f"""
            UPDATE users
            SET {", ".join(assignments)}
            WHERE {role_filter}
            """
        )
    )


def downgrade() -> None:
    # This is a production safety invariant. Downgrade intentionally does not
    # make bootstrap platform owners inactive or unverifiable again.
    pass
