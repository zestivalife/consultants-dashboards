from __future__ import annotations

import asyncio
import os

import asyncpg


TARGET_ALEMBIC_REVISION = "d3e4f5a6b7c8"


def _database_url() -> str:
    url = os.environ["DATABASE_URL"]
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _execute(conn: asyncpg.Connection, statement: str) -> None:
    await conn.execute(statement)


async def reconcile() -> None:
    conn = await asyncpg.connect(_database_url())
    try:
        await _execute(conn, "CREATE EXTENSION IF NOT EXISTS pgcrypto")

        user_columns = {
            "company_name": "VARCHAR(255)",
            "location": "VARCHAR(255)",
            "employees": "INTEGER",
            "industry": "VARCHAR(255)",
            "first_name": "VARCHAR(100)",
            "last_name": "VARCHAR(100)",
            "phone": "VARCHAR(20)",
            "mobile": "VARCHAR(20)",
            "avatar_url": "VARCHAR(500)",
            "status": "VARCHAR(40) NOT NULL DEFAULT 'ACTIVE'",
            "permissions": "JSON NOT NULL DEFAULT '[]'::json",
            "company_id": "UUID",
            "last_login_at": "TIMESTAMPTZ",
            "last_login": "TIMESTAMPTZ",
            "deleted_at": "TIMESTAMPTZ",
            "email_verified": "BOOLEAN NOT NULL DEFAULT false",
            "mobile_verified": "BOOLEAN NOT NULL DEFAULT false",
            "remember_me": "BOOLEAN NOT NULL DEFAULT false",
            "password_changed_at": "TIMESTAMPTZ",
            "mfa_enabled": "BOOLEAN NOT NULL DEFAULT false",
            "current_session_version": "INTEGER NOT NULL DEFAULT 1",
            "refresh_token_version": "INTEGER NOT NULL DEFAULT 1",
            "is_active": "BOOLEAN NOT NULL DEFAULT true",
        }
        for column_name, column_sql in user_columns.items():
            await _execute(conn, f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_sql}")
        await _execute(conn, "UPDATE users SET email_verified = is_verified WHERE email_verified = false")
        await _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_mobile ON users (mobile) WHERE mobile IS NOT NULL")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_users_status ON users (status)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(255) NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS permissions (
                id UUID PRIMARY KEY,
                key VARCHAR(120) NOT NULL UNIQUE,
                module VARCHAR(80) NOT NULL,
                label VARCHAR(120) NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_permissions_key ON permissions (key)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_permissions_module ON permissions (module)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                id UUID PRIMARY KEY,
                role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_role_permission ON role_permissions (role_id, permission_id)",
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS auth_audit_logs (
                id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                event_type VARCHAR(100) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN NOT NULL DEFAULT false,
                details JSON DEFAULT '{}'::json,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_user_id ON auth_audit_logs (user_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_event_type ON auth_audit_logs (event_type)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_created_at ON auth_audit_logs (created_at)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS login_sessions (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                refresh_token_id UUID REFERENCES refresh_tokens(id) ON DELETE SET NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                browser VARCHAR(120),
                platform VARCHAR(120),
                device_label VARCHAR(160),
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                revoked_at TIMESTAMPTZ
            )
            """,
        )
        await _execute(conn, "ALTER TABLE login_sessions ADD COLUMN IF NOT EXISTS device_label VARCHAR(160)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_login_sessions_user_id ON login_sessions (user_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_login_sessions_status ON login_sessions (status)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS departments (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_department_org_name ON departments (organization_id, name)",
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY,
                key VARCHAR(80) NOT NULL UNIQUE,
                name VARCHAR(120) NOT NULL UNIQUE,
                description TEXT,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            """
            INSERT INTO products (id, key, name, description, status, created_at, updated_at)
            VALUES
                ('10000000-0000-0000-0000-000000000001', 'nuetra', 'Nuetra', 'Core adaptive nutrition and recovery platform', 'ACTIVE', now(), now()),
                ('10000000-0000-0000-0000-000000000002', 'fiteatsy', 'FitEatsy', 'Nutrition and habit product line for lifestyle recovery programs', 'ACTIVE', now(), now())
            ON CONFLICT (key) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, status = EXCLUDED.status, updated_at = now()
            """,
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_invitations (
                id UUID PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                invited_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
                organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
                invited_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                product_id UUID REFERENCES products(id) ON DELETE SET NULL,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
                token VARCHAR(120) NOT NULL DEFAULT '',
                token_hash VARCHAR(64),
                token_fingerprint VARCHAR(16),
                expires_at TIMESTAMPTZ,
                accepted_at TIMESTAMPTZ,
                last_sent_at TIMESTAMPTZ,
                cancelled_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        invitation_columns = {
            "first_name": "VARCHAR(120)",
            "last_name": "VARCHAR(120)",
            "mobile_number": "VARCHAR(40)",
            "country_code": "VARCHAR(8)",
            "user_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
            "product_id": "UUID REFERENCES products(id) ON DELETE SET NULL",
            "token_hash": "VARCHAR(64)",
            "token_fingerprint": "VARCHAR(16)",
            "last_sent_at": "TIMESTAMPTZ",
            "cancelled_at": "TIMESTAMPTZ",
            "updated_at": "TIMESTAMPTZ NOT NULL DEFAULT now()",
        }
        for column_name, column_sql in invitation_columns.items():
            await _execute(conn, f"ALTER TABLE user_invitations ADD COLUMN IF NOT EXISTS {column_name} {column_sql}")
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token_hash = encode(digest(NULLIF(token, ''), 'sha256'), 'hex')
            WHERE token_hash IS NULL AND NULLIF(token, '') IS NOT NULL
            """,
        )
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token = 'redacted:' || id::text
            WHERE token_hash IS NOT NULL AND token NOT LIKE 'redacted:%'
            """,
        )
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token_fingerprint = substring(token_hash from 1 for 12)
            WHERE token_hash IS NOT NULL AND token_fingerprint IS NULL
            """,
        )
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token_hash = encode(digest(id::text || ':' || email, 'sha256'), 'hex'),
                token = 'redacted:' || id::text,
                token_fingerprint = substring(encode(digest(id::text || ':' || email, 'sha256'), 'hex') from 1 for 12)
            WHERE token_hash IS NULL
            """
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_invitations_email ON user_invitations (email)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_invitations_status ON user_invitations (status)")
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_invitations_token_hash ON user_invitations (token_hash)",
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS invitation_email_outbox (
                id UUID PRIMARY KEY,
                invitation_id UUID REFERENCES user_invitations(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                event_type VARCHAR(80) NOT NULL,
                status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
                payload JSON NOT NULL DEFAULT '{}'::json,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS password_history (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )

        await _execute(conn, "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
        current = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        if current:
            await conn.execute("UPDATE alembic_version SET version_num = $1", TARGET_ALEMBIC_REVISION)
        else:
            await conn.execute("INSERT INTO alembic_version (version_num) VALUES ($1)", TARGET_ALEMBIC_REVISION)
        print(f"Auth schema reconciled and stamped at {TARGET_ALEMBIC_REVISION}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(reconcile())
