"""repair missing auth core tables after initial baseline

Revision ID: 0001a
Revises: 0001
Create Date: 2026-07-09
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0001a"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id UUID PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name, description, created_at, updated_at)
        VALUES (gen_random_uuid(), 'member', 'Default member role', now(), now())
        ON CONFLICT (name) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, name, description, created_at, updated_at)
        VALUES (gen_random_uuid(), 'admin', 'Administrator role', now(), now())
        ON CONFLICT (name) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role_id UUID NOT NULL REFERENCES roles(id),
            is_verified BOOLEAN NOT NULL DEFAULT false,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
            lock_until TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS otp_verifications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            purpose VARCHAR(50) NOT NULL,
            verified_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS consents (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            consent_type VARCHAR(100) NOT NULL,
            accepted_at TIMESTAMPTZ NOT NULL,
            version VARCHAR(20) NULL
        )
        """
    )


def downgrade() -> None:
    # This is a repair migration for inconsistent baseline databases and should not
    # destructively remove baseline auth tables during rollback.
    pass
