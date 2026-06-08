"""add team roles: team_lead, team_member

Revision ID: 53600889d4e0
Revises: 53600889d4d9
Create Date: 2026-03-29 19:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53600889d4e0'
down_revision: Union[str, None] = '53600889d4d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Seed the team_lead role
    op.execute(
        "INSERT INTO roles (id, name, description, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'team_lead', 'Team leader who can manage their team', now(), now()) "
        "ON CONFLICT (name) DO NOTHING"
    )
    # Seed the team_member role
    op.execute(
        "INSERT INTO roles (id, name, description, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'team_member', 'Standard team member', now(), now()) "
        "ON CONFLICT (name) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('team_lead', 'team_member')")
