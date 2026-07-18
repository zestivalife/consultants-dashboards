"""repair user identity columns

Revision ID: c0d1e2f3a4b5
Revises: b8c9d0e1f2a3
Create Date: 2026-07-18 16:45:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c0d1e2f3a4b5"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


IDENTITY_COLUMNS: tuple[tuple[str, sa.Column], ...] = (
    ("mobile", sa.Column("mobile", sa.String(length=20), nullable=True)),
    ("email_verified", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("mobile_verified", sa.Column("mobile_verified", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("remember_me", sa.Column("remember_me", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("last_login", sa.Column("last_login", sa.DateTime(timezone=True), nullable=True)),
    ("password_changed_at", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True)),
    ("mfa_enabled", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("current_session_version", sa.Column("current_session_version", sa.Integer(), nullable=False, server_default="1")),
    ("refresh_token_version", sa.Column("refresh_token_version", sa.Integer(), nullable=False, server_default="1")),
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    for column_name, column in IDENTITY_COLUMNS:
        if column_name not in existing_columns:
            op.add_column("users", column)

    refreshed_columns = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if {"email_verified", "is_verified"}.issubset(refreshed_columns):
        op.execute("UPDATE users SET email_verified = is_verified WHERE email_verified = false")

    existing_constraints = {constraint["name"] for constraint in sa.inspect(bind).get_unique_constraints("users")}
    if "uq_users_mobile" not in existing_constraints:
        op.create_unique_constraint("uq_users_mobile", "users", ["mobile"])

    for column_name in [
        "email_verified",
        "mobile_verified",
        "remember_me",
        "mfa_enabled",
        "current_session_version",
        "refresh_token_version",
    ]:
        if column_name in refreshed_columns:
            op.alter_column("users", column_name, server_default=None)


def downgrade() -> None:
    # This is a production schema-repair migration for columns that are part of the
    # canonical identity model. Dropping them during rollback would risk data loss
    # in environments where the original c9d0e1f2a3b4 migration already succeeded.
    pass
