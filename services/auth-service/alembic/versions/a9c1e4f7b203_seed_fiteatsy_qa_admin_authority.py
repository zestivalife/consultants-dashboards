"""seed delegated Fiteatsy QA Admin authority

Revision ID: a9c1e4f7b203
Revises: f7b8c9d0e1f2
"""

from alembic import op
import sqlalchemy as sa


revision = "a9c1e4f7b203"
down_revision = "f7b8c9d0e1f2"
branch_labels = None
depends_on = None

PERMISSION_KEY = "fiteatsy.qa.admin.create"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (id, key, module, label, description, created_at, updated_at)
            VALUES (
                gen_random_uuid(), :key, 'fiteatsy', 'Provision Fiteatsy QA Admin',
                'Provision a non-clinical QA_TEST administrator through delegated authority', now(), now()
            )
            ON CONFLICT (key) DO NOTHING
            """
        ),
        {"key": PERMISSION_KEY},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (id, role_id, permission_id, created_at)
            SELECT gen_random_uuid(), roles.id, permissions.id, now()
            FROM roles CROSS JOIN permissions
            WHERE roles.name = 'platform_owner' AND permissions.key = :key
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
              AND roles.name = 'platform_owner'
              AND permissions.key = :key
            """
        ),
        {"key": PERMISSION_KEY},
    )
    conn.execute(sa.text("DELETE FROM permissions WHERE key = :key"), {"key": PERMISSION_KEY})
