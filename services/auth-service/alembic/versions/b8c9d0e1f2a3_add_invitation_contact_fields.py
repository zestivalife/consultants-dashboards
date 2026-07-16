"""add invitation contact fields

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-16 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_invitations", sa.Column("first_name", sa.String(length=120), nullable=True))
    op.add_column("user_invitations", sa.Column("last_name", sa.String(length=120), nullable=True))
    op.add_column("user_invitations", sa.Column("mobile_number", sa.String(length=40), nullable=True))
    op.add_column("user_invitations", sa.Column("country_code", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("user_invitations", "country_code")
    op.drop_column("user_invitations", "mobile_number")
    op.drop_column("user_invitations", "last_name")
    op.drop_column("user_invitations", "first_name")
