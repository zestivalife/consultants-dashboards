"""seed platform superusers

Revision ID: b1c2d3e4f5a6
Revises: 8d2d6e9a1c11
Create Date: 2026-07-09 11:10:00
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "8d2d6e9a1c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO users (
            id,
            email,
            password_hash,
            role_id,
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
        SELECT
            'a6d61a4e-4d1d-4d45-93fb-d0ef4fc3e001'::uuid,
            'zestivapriyanshi@gmail.com',
            '$2b$12$0efzkqPBVgbqscCjtLWRNeJ.8sa1U5tVdkK9MUZT0OEtSg3ICRQqq',
            roles.id,
            true,
            0,
            NULL,
            'Priyanshi',
            NULL,
            NULL,
            NULL,
            now(),
            now()
        FROM roles
        WHERE roles.name = 'superuser'
        ON CONFLICT (email) DO UPDATE
        SET
            password_hash = EXCLUDED.password_hash,
            role_id = EXCLUDED.role_id,
            is_verified = EXCLUDED.is_verified,
            failed_login_attempts = 0,
            lock_until = NULL,
            first_name = EXCLUDED.first_name,
            updated_at = now()
        """
    )

    op.execute(
        """
        INSERT INTO users (
            id,
            email,
            password_hash,
            role_id,
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
        SELECT
            'a6d61a4e-4d1d-4d45-93fb-d0ef4fc3e002'::uuid,
            'lalitppaunikar26@gmail.com',
            '$2b$12$MGuGMPCguKCGN7xOvtVKFuRAVL2p/zj0WqX3XuqEcLFpnD/zrqfwC',
            roles.id,
            true,
            0,
            NULL,
            'Lalit',
            NULL,
            NULL,
            NULL,
            now(),
            now()
        FROM roles
        WHERE roles.name = 'superuser'
        ON CONFLICT (email) DO UPDATE
        SET
            password_hash = EXCLUDED.password_hash,
            role_id = EXCLUDED.role_id,
            is_verified = EXCLUDED.is_verified,
            failed_login_attempts = 0,
            lock_until = NULL,
            first_name = EXCLUDED.first_name,
            updated_at = now()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM users
        WHERE email IN (
            'zestivapriyanshi@gmail.com',
            'lalitppaunikar26@gmail.com'
        )
        """
    )
