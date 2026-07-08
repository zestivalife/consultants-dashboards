"""add consultant and platform admin roles

Revision ID: 8d2d6e9a1c11
Revises: 3a0b0ac6995c
Create Date: 2026-07-08 23:45:00
"""
from typing import Sequence, Union

from alembic import op


revision: str = "8d2d6e9a1c11"
down_revision: Union[str, None] = "3a0b0ac6995c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for name, description in [
        ("consultant", "Consultant access for practitioner workflows"),
        ("provider", "Provider access for practitioner workflows"),
        ("dietician", "Dietician access for practitioner workflows"),
        ("senior_consultant", "Senior consultant with review permissions"),
        ("corporate_admin", "Corporate administrator access"),
        ("organization_admin", "Organization administrator access"),
        ("superuser", "Platform superuser access"),
    ]:
        op.execute(
            "INSERT INTO roles (id, name, description, created_at, updated_at) "
            f"VALUES (gen_random_uuid(), '{name}', '{description}', now(), now()) "
            "ON CONFLICT (name) DO NOTHING"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM roles WHERE name IN "
        "('consultant', 'provider', 'dietician', 'senior_consultant', 'corporate_admin', 'organization_admin', 'superuser')"
    )
