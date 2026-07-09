"""seed platform owner accounts

Revision ID: c4d5e6f7a8b9
Revises: b1c2d3e4f5a6
Create Date: 2026-07-09 15:05:00
"""
from typing import Sequence, Union
import hashlib
import uuid

import bcrypt
import sqlalchemy as sa
from alembic import op


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLATFORM_OWNER_ROLE = "PLATFORM_OWNER"
PLATFORM_OWNER_DESC = "Platform owner with full system permissions across companies, mentors, consultants, and admins"
OWNER_USERS = [
    {
        "id": uuid.UUID("66f4d9d8-6f1f-4d39-a101-5355d5950001"),
        "email": "zestivapriyanshi@gmail.com",
        "password": "Priyanshi@123",
        "first_name": "Priyanshi",
    },
    {
        "id": uuid.UUID("66f4d9d8-6f1f-4d39-a101-5355d5950002"),
        "email": "lalitppaunikar26@gmail.com",
        "password": "Lalit@123",
        "first_name": "Lalit",
    },
]


def _hash_password(password: str) -> str:
    prehashed = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
    return bcrypt.hashpw(prehashed, bcrypt.gensalt(rounds=12)).decode("utf-8")


def _has_column(conn: sa.Connection, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(conn)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    conn = op.get_bind()

    if not _has_column(conn, "users", "is_active"):
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.alter_column("users", "is_active", server_default=None)

    conn.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, description, created_at, updated_at)
            VALUES (:id, :name, :description, now(), now())
            ON CONFLICT (name) DO UPDATE
            SET
                description = EXCLUDED.description,
                updated_at = now()
            """
        ),
        {
            "id": uuid.uuid4(),
            "name": PLATFORM_OWNER_ROLE,
            "description": PLATFORM_OWNER_DESC,
        },
    )

    role_id = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = :name"),
        {"name": PLATFORM_OWNER_ROLE},
    ).scalar_one()

    for owner in OWNER_USERS:
        conn.execute(
            sa.text(
                """
                INSERT INTO users (
                    id,
                    email,
                    password_hash,
                    role_id,
                    is_active,
                    is_verified,
                    failed_login_attempts,
                    lock_until,
                    first_name,
                    last_name,
                    phone,
                    company_id,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :email,
                    :password_hash,
                    :role_id,
                    true,
                    true,
                    0,
                    NULL,
                    :first_name,
                    NULL,
                    NULL,
                    NULL,
                    now(),
                    now()
                )
                ON CONFLICT (email) DO UPDATE
                SET
                    password_hash = EXCLUDED.password_hash,
                    role_id = EXCLUDED.role_id,
                    is_active = true,
                    is_verified = true,
                    failed_login_attempts = 0,
                    lock_until = NULL,
                    first_name = EXCLUDED.first_name,
                    updated_at = now()
                """
            ),
            {
                "id": owner["id"],
                "email": owner["email"],
                "password_hash": _hash_password(owner["password"]),
                "role_id": role_id,
                "first_name": owner["first_name"],
            },
        )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
            DELETE FROM users
            WHERE email IN :emails
            """
        ).bindparams(sa.bindparam("emails", expanding=True)),
        {"emails": [owner["email"] for owner in OWNER_USERS]},
    )

    remaining_platform_owner_users = conn.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role_id = (SELECT id FROM roles WHERE name = :name)
            """
        ),
        {"name": PLATFORM_OWNER_ROLE},
    ).scalar_one()

    if remaining_platform_owner_users == 0:
        conn.execute(
            sa.text("DELETE FROM roles WHERE name = :name"),
            {"name": PLATFORM_OWNER_ROLE},
        )
