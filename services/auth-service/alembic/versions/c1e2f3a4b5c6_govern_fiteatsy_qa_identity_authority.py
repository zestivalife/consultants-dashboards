"""govern delegated Fiteatsy QA identity authority

Revision ID: c1e2f3a4b5c6
Revises: b0d2f6a8c401
"""

from alembic import op
import sqlalchemy as sa


revision = "c1e2f3a4b5c6"
down_revision = "b0d2f6a8c401"
branch_labels = None
depends_on = None

PERMISSIONS = (
    (
        "fiteatsy.qa.identity.create",
        "Provision Fiteatsy QA identity",
        "Provision a governed non-clinical QA_TEST identity through delegated authority",
    ),
    (
        "fiteatsy.qa.session.issue",
        "Issue Fiteatsy QA session",
        "Issue an audited short-lived session for a governed QA_TEST identity",
    ),
)

CANONICAL_OWNER_IDS = (
    "66f4d9d8-6f1f-4d39-a101-5355d5950001",
    "66f4d9d8-6f1f-4d39-a101-5355d5950002",
)


def upgrade() -> None:
    conn = op.get_bind()
    for key, label, description in PERMISSIONS:
        conn.execute(
            sa.text(
                """
                INSERT INTO permissions (id, key, module, label, description, created_at, updated_at)
                VALUES (gen_random_uuid(), :key, 'fiteatsy', :label, :description, now(), now())
                ON CONFLICT (key) DO UPDATE
                SET module = EXCLUDED.module,
                    label = EXCLUDED.label,
                    description = EXCLUDED.description,
                    updated_at = now()
                """
            ),
            {"key": key, "label": label, "description": description},
        )

    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (id, role_id, permission_id, created_at)
            SELECT gen_random_uuid(), r.id, p.id, now()
            FROM roles r
            CROSS JOIN permissions p
            WHERE lower(r.name) = 'platform_owner'
              AND p.key IN ('fiteatsy.qa.identity.create', 'fiteatsy.qa.session.issue')
            ON CONFLICT (role_id, permission_id) DO NOTHING
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions rp
            USING roles r, permissions p
            WHERE rp.role_id = r.id
              AND rp.permission_id = p.id
              AND p.key IN ('fiteatsy.qa.identity.create', 'fiteatsy.qa.session.issue')
              AND lower(r.name) <> 'platform_owner'
            """
        )
    )

    conn.execute(
        sa.text(
            """
            UPDATE users
            SET role_id = (SELECT id FROM roles WHERE lower(name) = 'platform_owner' LIMIT 1),
                updated_at = now()
            WHERE id IN (CAST(:owner_id_1 AS uuid), CAST(:owner_id_2 AS uuid))
            """
        ),
        {"owner_id_1": CANONICAL_OWNER_IDS[0], "owner_id_2": CANONICAL_OWNER_IDS[1]},
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM user_roles
            WHERE user_id IN (CAST(:owner_id_1 AS uuid), CAST(:owner_id_2 AS uuid))
              AND role_id = (SELECT id FROM roles WHERE lower(name) = 'superuser' LIMIT 1)
            """
        ),
        {"owner_id_1": CANONICAL_OWNER_IDS[0], "owner_id_2": CANONICAL_OWNER_IDS[1]},
    )
    conn.execute(
        sa.text(
            """
            UPDATE user_roles
            SET is_primary = false
            WHERE user_id IN (CAST(:owner_id_1 AS uuid), CAST(:owner_id_2 AS uuid))
            """
        ),
        {"owner_id_1": CANONICAL_OWNER_IDS[0], "owner_id_2": CANONICAL_OWNER_IDS[1]},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO user_roles (id, user_id, role_id, assigned_by_user_id, is_primary, created_at)
            SELECT gen_random_uuid(), u.id, r.id, u.id, true, now()
            FROM users u
            CROSS JOIN roles r
            WHERE u.id IN (CAST(:owner_id_1 AS uuid), CAST(:owner_id_2 AS uuid))
              AND lower(r.name) = 'platform_owner'
            ON CONFLICT (user_id, role_id) DO UPDATE SET is_primary = true
            """
        ),
        {"owner_id_1": CANONICAL_OWNER_IDS[0], "owner_id_2": CANONICAL_OWNER_IDS[1]},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions rp
            USING permissions p
            WHERE rp.permission_id = p.id
              AND p.key IN ('fiteatsy.qa.identity.create', 'fiteatsy.qa.session.issue')
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE key IN ('fiteatsy.qa.identity.create', 'fiteatsy.qa.session.issue')
            """
        )
    )
