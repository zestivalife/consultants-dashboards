"""restore platform owner bootstrap accounts

Revision ID: f7b8c9d0e1f2
Revises: f3a4b5c6d7e8
Create Date: 2026-08-13 10:45:00
"""
from __future__ import annotations

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

from app.core.security import hash_password


revision: str = "f7b8c9d0e1f2"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OWNER_USERS = [
    {
        "id": uuid.UUID("66f4d9d8-6f1f-4d39-a101-5355d5950001"),
        "email": "zestivapriyanshi@gmail.com",
        "password": "Priyanshi@123",
        "first_name": "Priyanshi",
        "last_name": None,
    },
    {
        "id": uuid.UUID("66f4d9d8-6f1f-4d39-a101-5355d5950002"),
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
    table_names = _table_names(conn)
    owner_role_id = _preferred_owner_role_id(conn)
    if owner_role_id is None:
        return

    for owner in OWNER_USERS:
        values = {
            "id": owner["id"],
            "email": owner["email"],
            "password_hash": hash_password(owner["password"]),
            "role_id": owner_role_id,
            "first_name": owner["first_name"],
            "last_name": owner["last_name"],
        }

        insert_columns = [
            "id",
            "email",
            "password_hash",
            "role_id",
            "is_active",
            "is_verified",
            "failed_login_attempts",
            "lock_until",
            "first_name",
            "created_at",
            "updated_at",
        ]
        insert_values = [
            ":id",
            ":email",
            ":password_hash",
            ":role_id",
            "true",
            "true",
            "0",
            "NULL",
            ":first_name",
            "now()",
            "now()",
        ]
        update_assignments = [
            "password_hash = EXCLUDED.password_hash",
            "role_id = EXCLUDED.role_id",
            "is_active = true",
            "is_verified = true",
            "failed_login_attempts = 0",
            "lock_until = NULL",
            "first_name = EXCLUDED.first_name",
            "updated_at = now()",
        ]

        if "last_name" in users_columns:
            insert_columns.append("last_name")
            insert_values.append(":last_name")
            update_assignments.append("last_name = EXCLUDED.last_name")
        if "email_verified" in users_columns:
            insert_columns.append("email_verified")
            insert_values.append("true")
            update_assignments.append("email_verified = true")
        if "status" in users_columns:
            insert_columns.append("status")
            insert_values.append("'ACTIVE'")
            update_assignments.append("status = 'ACTIVE'")
        if "deleted_at" in users_columns:
            insert_columns.append("deleted_at")
            insert_values.append("NULL")
            update_assignments.append("deleted_at = NULL")
        if "must_change_password" in users_columns:
            insert_columns.append("must_change_password")
            insert_values.append("false")
            update_assignments.append("must_change_password = false")
        if "credential_status" in users_columns:
            insert_columns.append("credential_status")
            insert_values.append("'PERMANENT'")
            update_assignments.append("credential_status = 'PERMANENT'")
        if "temporary_password_created_at" in users_columns:
            insert_columns.append("temporary_password_created_at")
            insert_values.append("NULL")
            update_assignments.append("temporary_password_created_at = NULL")
        if "temporary_password_expires_at" in users_columns:
            insert_columns.append("temporary_password_expires_at")
            insert_values.append("NULL")
            update_assignments.append("temporary_password_expires_at = NULL")
        if "temporary_password_consumed_at" in users_columns:
            insert_columns.append("temporary_password_consumed_at")
            insert_values.append("NULL")
            update_assignments.append("temporary_password_consumed_at = NULL")
        if "password_changed_at" in users_columns:
            insert_columns.append("password_changed_at")
            insert_values.append("now()")
            update_assignments.append("password_changed_at = now()")

        conn.execute(
            sa.text(
                f"""
                INSERT INTO users ({", ".join(insert_columns)})
                VALUES ({", ".join(insert_values)})
                ON CONFLICT (email) DO UPDATE
                SET {", ".join(update_assignments)}
                """
            ),
            values,
        )

    if "user_roles" in table_names:
        for owner in OWNER_USERS:
            user_id = conn.execute(
                sa.text("SELECT id FROM users WHERE lower(email) = lower(:email) LIMIT 1"),
                {"email": owner["email"]},
            ).scalar_one_or_none()
            if user_id is None:
                continue
            conn.execute(
                sa.text(
                    """
                    INSERT INTO user_roles (id, user_id, role_id, assigned_by_user_id, is_primary, created_at)
                    VALUES (:id, :user_id, :role_id, :user_id, true, now())
                    ON CONFLICT (user_id, role_id) DO UPDATE
                    SET is_primary = true
                    """
                ),
                {"id": uuid.uuid4(), "user_id": user_id, "role_id": owner_role_id},
            )


def downgrade() -> None:
    # Production bootstrap safety repair. Downgrade intentionally does not
    # remove or deactivate platform owner accounts.
    pass
