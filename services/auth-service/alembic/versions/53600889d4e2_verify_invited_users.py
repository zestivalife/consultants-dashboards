"""verify invited team_lead and team_member users

Revision ID: 53600889d4e2
Revises: 53600889d4e1
Create Date: 2026-04-13 00:00:00

Fix: Invited users (team_lead, team_member) were created with is_verified=False
but never received an OTP, so they could not log in. This migration marks all
existing invited users as verified so they can log in with their temp passwords.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '53600889d4e2'
down_revision: Union[str, None] = '53600889d4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Mark all team_lead and team_member users as verified.
    # These users were invited by corporate admins and never received an OTP,
    # so is_verified=False was blocking them from logging in entirely.
    op.execute(
        """
        UPDATE users
        SET is_verified = TRUE
        WHERE is_verified = FALSE
          AND role_id IN (
              SELECT id FROM roles WHERE name IN ('team_lead', 'team_member')
          )
        """
    )


def downgrade() -> None:
    # Cannot safely reverse - we don't know which users were previously unverified.
    pass
