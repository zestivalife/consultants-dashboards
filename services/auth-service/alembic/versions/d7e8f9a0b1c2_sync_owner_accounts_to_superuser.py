"""sync owner accounts to superuser

Revision ID: d7e8f9a0b1c2
Revises: c4d5e6f7a8b9
Create Date: 2026-07-09 16:35:00
"""
from typing import Sequence, Union
import hashlib

import bcrypt
import sqlalchemy as sa
from alembic import op


revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OWNER_USERS = [
    {
        "email": "zestivapriyanshi@gmail.com",
        "password": "Priyanshi@123",
        "first_name": "Priyanshi",
    },
    {
        "email": "lalitppaunikar26@gmail.com",
        "password": "Lalit@123",
        "first_name": "Lalit",
    },
]


def _hash_password(password: str) -> str:
    prehashed = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
    return bcrypt.hashpw(prehashed, bcrypt.gensalt(rounds=12)).decode("utf-8")


def upgrade() -> None:
    conn = op.get_bind()
    superuser_role_id = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = :name"),
        {"name": "superuser"},
    ).scalar_one()

    has_is_active = any(
        column["name"] == "is_active"
        for column in sa.inspect(conn).get_columns("users")
    )

    for owner in OWNER_USERS:
        if has_is_active:
            conn.execute(
                sa.text(
                    """
                    UPDATE users
                    SET
                        password_hash = :password_hash,
                        role_id = :role_id,
                        is_verified = true,
                        is_active = true,
                        failed_login_attempts = 0,
                        lock_until = NULL,
                        first_name = :first_name,
                        updated_at = now()
                    WHERE email = :email
                    """
                ),
                {
                    "email": owner["email"],
                    "password_hash": _hash_password(owner["password"]),
                    "role_id": superuser_role_id,
                    "first_name": owner["first_name"],
                },
            )
        else:
            conn.execute(
                sa.text(
                    """
                    UPDATE users
                    SET
                        password_hash = :password_hash,
                        role_id = :role_id,
                        is_verified = true,
                        failed_login_attempts = 0,
                        lock_until = NULL,
                        first_name = :first_name,
                        updated_at = now()
                    WHERE email = :email
                    """
                ),
                {
                    "email": owner["email"],
                    "password_hash": _hash_password(owner["password"]),
                    "role_id": superuser_role_id,
                    "first_name": owner["first_name"],
                },
            )


def downgrade() -> None:
    # Keep owner accounts intact on downgrade of this sync migration.
    pass
