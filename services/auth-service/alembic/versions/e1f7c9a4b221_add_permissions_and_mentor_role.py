"""add permissions column and mentor role

Revision ID: e1f7c9a4b221
Revises: d7e8f9a0b1c2
Create Date: 2026-07-10 12:05:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f7c9a4b221"
down_revision: Union[str, None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    user_columns = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "permissions" not in user_columns:
        op.add_column(
            "users",
            sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        )
        op.alter_column("users", "permissions", server_default=None)
    op.execute(
        "INSERT INTO roles (id, name, description, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'mentor', 'Mentor access for supervision and support workflows', now(), now()) "
        "ON CONFLICT (name) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name = 'mentor'")
    bind = op.get_bind()
    user_columns = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "permissions" in user_columns:
        op.drop_column("users", "permissions")
