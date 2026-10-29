"""Grant explicit Fiteatsy assignment authority to platform owners.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
"""

from alembic import op
import sqlalchemy as sa


revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("fiteatsy.client.assignment.read", "View Fiteatsy client assignments", "View eligible clients, professionals, and current assignments"),
    ("fiteatsy.client.assign", "Assign Fiteatsy clients", "Create and reassign governed Fiteatsy client relationships"),
    ("fiteatsy.client.assignment.revoke", "Revoke Fiteatsy client assignments", "End governed Fiteatsy client relationships"),
)


def upgrade() -> None:
    conn = op.get_bind()
    for key, label, description in PERMISSIONS:
        conn.execute(sa.text("""
            INSERT INTO permissions (id, key, module, label, description, created_at, updated_at)
            VALUES (gen_random_uuid(), :key, 'fiteatsy', :label, :description, now(), now())
            ON CONFLICT (key) DO UPDATE
            SET module = EXCLUDED.module, label = EXCLUDED.label,
                description = EXCLUDED.description, updated_at = now()
        """), {"key": key, "label": label, "description": description})
    conn.execute(sa.text("""
        INSERT INTO role_permissions (id, role_id, permission_id, created_at)
        SELECT gen_random_uuid(), roles.id, permissions.id, now()
        FROM roles CROSS JOIN permissions
        WHERE lower(roles.name) IN ('platform_owner', 'superuser', 'super_admin')
          AND permissions.key IN (
            'fiteatsy.client.assignment.read',
            'fiteatsy.client.assign',
            'fiteatsy.client.assignment.revoke'
          )
        ON CONFLICT (role_id, permission_id) DO NOTHING
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM role_permissions
        USING permissions
        WHERE role_permissions.permission_id = permissions.id
          AND permissions.key IN (
            'fiteatsy.client.assignment.read',
            'fiteatsy.client.assign',
            'fiteatsy.client.assignment.revoke'
          )
    """))
    conn.execute(sa.text("""
        DELETE FROM permissions WHERE key IN (
          'fiteatsy.client.assignment.read',
          'fiteatsy.client.assign',
          'fiteatsy.client.assignment.revoke'
        )
    """))
