"""grant delegated Fiteatsy QA Admin authority to canonical superuser

Revision ID: b0d2f6a8c401
Revises: a9c1e4f7b203
"""

from alembic import op
import sqlalchemy as sa


revision = "b0d2f6a8c401"
down_revision = "a9c1e4f7b203"
branch_labels = None
depends_on = None

PERMISSION_KEY = "fiteatsy.qa.admin.create"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (id, role_id, permission_id, created_at)
            SELECT gen_random_uuid(), roles.id, permissions.id, now()
            FROM roles CROSS JOIN permissions
            WHERE lower(roles.name) = 'superuser' AND permissions.key = :key
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        ),
        {"key": PERMISSION_KEY},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            USING roles, permissions
            WHERE role_permissions.role_id = roles.id
              AND role_permissions.permission_id = permissions.id
              AND lower(roles.name) = 'superuser'
              AND permissions.key = :key
            """
        ),
        {"key": PERMISSION_KEY},
    )
