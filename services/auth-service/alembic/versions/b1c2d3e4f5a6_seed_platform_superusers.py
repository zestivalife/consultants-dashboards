"""reserved platform owner seed placeholder

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
    # Intentionally left blank.
    # Platform owner accounts are seeded in a later dedicated migration so the
    # repository has a single authoritative credential source.
    pass


def downgrade() -> None:
    pass
