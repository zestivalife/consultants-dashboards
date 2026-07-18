"""repair auth runtime tables

Revision ID: d3e4f5a6b7c8
Revises: d2e3f4a5b6c7
Create Date: 2026-07-18 17:20:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names(conn: sa.Connection) -> set[str]:
    return set(sa.inspect(conn).get_table_names())


def _column_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns(table_name)}


def _index_names(conn: sa.Connection, table_name: str) -> set[str]:
    return {index["name"] for index in sa.inspect(conn).get_indexes(table_name)}


def _add_column_if_missing(conn: sa.Connection, table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(conn, table_name):
        op.add_column(table_name, column)


def _create_index_if_missing(conn: sa.Connection, index_name: str, table_name: str, columns: list[str]) -> None:
    if index_name not in _index_names(conn, table_name):
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    conn = op.get_bind()
    tables = _table_names(conn)

    if "auth_audit_logs" not in tables:
        op.execute(
            """
            CREATE TABLE auth_audit_logs (
                id UUID PRIMARY KEY,
                user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
                event_type VARCHAR(50) NOT NULL,
                ip_address VARCHAR(45) NULL,
                user_agent TEXT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    else:
        _add_column_if_missing(conn, "auth_audit_logs", sa.Column("user_id", sa.Uuid(), nullable=True))
        _add_column_if_missing(conn, "auth_audit_logs", sa.Column("event_type", sa.String(length=50), nullable=True))
        _add_column_if_missing(conn, "auth_audit_logs", sa.Column("ip_address", sa.String(length=45), nullable=True))
        _add_column_if_missing(conn, "auth_audit_logs", sa.Column("user_agent", sa.Text(), nullable=True))
        _add_column_if_missing(conn, "auth_audit_logs", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        conn.execute(sa.text("UPDATE auth_audit_logs SET event_type = 'UNKNOWN' WHERE event_type IS NULL"))
        conn.execute(sa.text("UPDATE auth_audit_logs SET created_at = now() WHERE created_at IS NULL"))
        op.alter_column("auth_audit_logs", "event_type", existing_type=sa.String(length=50), nullable=False)
        op.alter_column("auth_audit_logs", "created_at", existing_type=sa.DateTime(timezone=True), nullable=False)

    _create_index_if_missing(conn, "ix_auth_audit_logs_event_type", "auth_audit_logs", ["event_type"])
    _create_index_if_missing(conn, "ix_auth_audit_logs_user_id", "auth_audit_logs", ["user_id"])

    if "refresh_tokens" not in tables:
        op.execute(
            """
            CREATE TABLE refresh_tokens (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(255) NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    _create_index_if_missing(conn, "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    if "permissions" not in tables:
        op.execute(
            """
            CREATE TABLE permissions (
                id UUID PRIMARY KEY,
                key VARCHAR(120) NOT NULL UNIQUE,
                module VARCHAR(80) NOT NULL,
                label VARCHAR(120) NOT NULL,
                description TEXT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    _create_index_if_missing(conn, "ix_permissions_key", "permissions", ["key"])
    _create_index_if_missing(conn, "ix_permissions_module", "permissions", ["module"])

    if "role_permissions" not in tables:
        op.execute(
            """
            CREATE TABLE role_permissions (
                id UUID PRIMARY KEY,
                role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
            )
            """
        )

    if "login_sessions" not in tables:
        op.execute(
            """
            CREATE TABLE login_sessions (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                refresh_token_id UUID NULL REFERENCES refresh_tokens(id) ON DELETE SET NULL,
                ip_address VARCHAR(45) NULL,
                user_agent TEXT NULL,
                browser VARCHAR(120) NULL,
                platform VARCHAR(120) NULL,
                device_label VARCHAR(160) NULL,
                status VARCHAR(40) NOT NULL,
                last_seen_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ NULL
            )
            """
        )
    else:
        _add_column_if_missing(conn, "login_sessions", sa.Column("device_label", sa.String(length=160), nullable=True))

    _create_index_if_missing(conn, "ix_login_sessions_user_id", "login_sessions", ["user_id"])
    _create_index_if_missing(conn, "ix_login_sessions_status", "login_sessions", ["status"])


def downgrade() -> None:
    # This is a production schema repair for runtime auth dependencies. Downgrade
    # is intentionally non-destructive to avoid removing login/audit history.
    pass
