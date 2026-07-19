"""reactivate platform owner accounts

Revision ID: d4e5f6a7b8c9
Revises: d3e4f5a6b7c8
Create Date: 2026-07-19 00:00:00
"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

from app.core.security import hash_password


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OWNER_USERS = [
    {
        "email": "zestivapriyanshi@gmail.com",
        "password": "Priyanshi@123",
        "first_name": "Priyanshi",
        "last_name": None,
    },
    {
        "email": "lalitppaunikar26@gmail.com",
        "password": "Lalit@123",
        "first_name": "Lalit",
        "last_name": "Paunikar",
    },
]


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def _table_names(conn: sa.Connection) -> set[str]:
    return set(sa.inspect(conn).get_table_names())


def _preferred_owner_role_id(conn: sa.Connection):
    return conn.execute(
        sa.text(
            """
            SELECT id
            FROM roles
            WHERE lower(name) IN ('superuser', 'platform_owner')
            ORDER BY CASE lower(name)
                WHEN 'superuser' THEN 1
                WHEN 'platform_owner' THEN 2
                ELSE 3
            END
            LIMIT 1
            """
        )
    ).scalar_one_or_none()


def upgrade() -> None:
    conn = op.get_bind()
    users_columns = _column_names(conn, "users")
    owner_role_id = _preferred_owner_role_id(conn)

    for owner in OWNER_USERS:
        values = {
            "email": owner["email"],
            "password_hash": hash_password(owner["password"]),
            "first_name": owner["first_name"],
            "last_name": owner["last_name"],
            "role_id": owner_role_id,
        }
        assignments = [
            "password_hash = :password_hash",
            "is_active = true",
            "is_verified = true",
            "failed_login_attempts = 0",
            "lock_until = NULL",
            "first_name = :first_name",
            "updated_at = now()",
        ]
        if "last_name" in users_columns:
            assignments.append("last_name = :last_name")
        if "email_verified" in users_columns:
            assignments.append("email_verified = true")
        if "status" in users_columns:
            assignments.append("status = 'ACTIVE'")
        if "deleted_at" in users_columns:
            assignments.append("deleted_at = NULL")
        if owner_role_id is not None:
            assignments.append("role_id = :role_id")

        conn.execute(
            sa.text(
                f"""
                UPDATE users
                SET {", ".join(assignments)}
                WHERE lower(email) = lower(:email)
                """
            ),
            values,
        )

    if owner_role_id is None or "user_roles" not in _table_names(conn):
        return

    owner_rows = conn.execute(
        sa.text(
            """
            SELECT id
            FROM users
            WHERE lower(email) IN (
                'zestivapriyanshi@gmail.com',
                'lalitppaunikar26@gmail.com'
            )
            """
        )
    ).fetchall()
    for row in owner_rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO user_roles (id, user_id, role_id, assigned_by_user_id, is_primary, created_at)
                VALUES (:id, :user_id, :role_id, :user_id, true, now())
                ON CONFLICT DO NOTHING
                """
            ),
            {"id": uuid.uuid4(), "user_id": row.id, "role_id": owner_role_id},
        )


def downgrade() -> None:
    # Owner reactivation is a production data repair. Downgrade intentionally
    # does not deactivate permanent platform owner accounts.
    pass
