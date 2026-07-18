"""create people and access foundation

Revision ID: f2b1c4d5e6f7
Revises: e1f7c9a4b221
Create Date: 2026-07-10 15:40:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f2b1c4d5e6f7"
down_revision: Union[str, None] = "e1f7c9a4b221"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_SEEDS = [
    ("platform_owner", "Platform owner with full system permissions"),
    ("organization_admin", "Organization administrator"),
    ("corporate_admin", "Corporate administrator"),
    ("practitioner", "Practitioner access"),
    ("mentor", "Mentor access"),
    ("consultant", "Consultant access"),
    ("senior_consultant", "Senior consultant access"),
    ("employee", "Employee access"),
    ("support_admin", "Support administrator"),
    ("superuser", "Platform superuser access"),
]

PERMISSION_SEEDS = [
    ("users.read", "users", "View users", "Read people records"),
    ("users.create", "users", "Create users", "Create workforce identities"),
    ("users.edit", "users", "Edit users", "Edit workforce identities"),
    ("users.delete", "users", "Delete users", "Soft delete workforce identities"),
    ("users.invite", "users", "Invite users", "Send platform invitations"),
    ("users.export", "users", "Export users", "Export workforce data"),
    ("users.import", "users", "Import users", "Bulk import workforce data"),
    ("users.reset_password", "users", "Reset password", "Reset workforce passwords"),
    ("users.force_logout", "users", "Force logout", "Terminate user sessions"),
    ("organizations.manage", "organizations", "Manage organizations", "Create and update organizations"),
    ("packages.manage", "packages", "Manage packages", "Manage package assignments"),
    ("services.manage", "services", "Manage services", "Manage service assignments"),
    ("reports.view", "reports", "View reports", "View analytics and reports"),
    ("audit.view", "audit", "View audit", "View audit events"),
    ("settings.manage", "settings", "Manage settings", "Manage workspace settings"),
    ("notifications.manage", "notifications", "Manage notifications", "Manage platform notifications"),
    ("subscriptions.manage", "subscriptions", "Manage subscriptions", "Manage subscription lifecycle"),
]

ROLE_PERMISSION_MAP = {
    "platform_owner": [seed[0] for seed in PERMISSION_SEEDS],
    "superuser": [seed[0] for seed in PERMISSION_SEEDS],
    "support_admin": ["users.read", "users.edit", "reports.view", "audit.view", "notifications.manage"],
    "organization_admin": ["users.read", "users.create", "users.edit", "users.invite", "users.export", "reports.view"],
    "corporate_admin": ["users.read", "users.create", "users.edit", "users.invite", "users.export", "reports.view", "organizations.manage"],
    "practitioner": ["users.read", "reports.view"],
    "mentor": ["users.read", "reports.view"],
    "consultant": ["users.read", "reports.view"],
    "senior_consultant": ["users.read", "reports.view", "users.export"],
    "employee": [],
}


def upgrade() -> None:
    conn = op.get_bind()
    _add_column_if_missing(conn, "users", "avatar_url", "VARCHAR(500)")
    _add_column_if_missing(conn, "users", "status", "VARCHAR(40) NOT NULL DEFAULT 'ACTIVE'")
    _add_column_if_missing(conn, "users", "last_login_at", "TIMESTAMPTZ")
    _add_column_if_missing(conn, "users", "deleted_at", "TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_status ON users (status)")
    op.execute("CREATE TABLE IF NOT EXISTS permissions (id UUID PRIMARY KEY, key VARCHAR(120) NOT NULL UNIQUE, module VARCHAR(80) NOT NULL, label VARCHAR(120) NOT NULL, description TEXT, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_permissions_key ON permissions (key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_permissions_module ON permissions (module)")
    op.execute("CREATE TABLE IF NOT EXISTS role_permissions (id UUID PRIMARY KEY, role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE, permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE, created_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id))")
    op.execute("CREATE TABLE IF NOT EXISTS user_roles (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE, assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL, is_primary BOOLEAN NOT NULL DEFAULT false, created_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_user_role UNIQUE (user_id, role_id))")
    op.execute("CREATE TABLE IF NOT EXISTS organizations (id UUID PRIMARY KEY, name VARCHAR(255) NOT NULL UNIQUE, logo_url TEXT, industry VARCHAR(255), company_size VARCHAR(80), gst_number VARCHAR(50), address TEXT, timezone_name VARCHAR(80), country VARCHAR(100), subscription_name VARCHAR(255), renewal_date DATE, primary_contact_name VARCHAR(255), primary_contact_email VARCHAR(255), status VARCHAR(40) NOT NULL, created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, deactivated_at TIMESTAMPTZ)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organizations_status ON organizations (status)")
    op.execute("CREATE TABLE IF NOT EXISTS departments (id UUID PRIMARY KEY, organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE, name VARCHAR(150) NOT NULL, description TEXT, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_department_org_name UNIQUE (organization_id, name))")
    op.execute("CREATE TABLE IF NOT EXISTS organization_memberships (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE, department_id UUID REFERENCES departments(id) ON DELETE SET NULL, employee_id VARCHAR(80), package_name VARCHAR(255), assigned_practitioner_id UUID REFERENCES users(id) ON DELETE SET NULL, assigned_mentor_id UUID REFERENCES users(id) ON DELETE SET NULL, assigned_consultant_id UUID REFERENCES users(id) ON DELETE SET NULL, status VARCHAR(40) NOT NULL, is_verified BOOLEAN NOT NULL DEFAULT false, tags JSONB NOT NULL DEFAULT '[]'::jsonb, created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL, joined_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, deactivated_at TIMESTAMPTZ, CONSTRAINT uq_user_organization_membership UNIQUE (user_id, organization_id))")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organization_memberships_employee_id ON organization_memberships (employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organization_memberships_status ON organization_memberships (status)")
    op.execute("CREATE TABLE IF NOT EXISTS audit_events (id UUID PRIMARY KEY, actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL, entity_type VARCHAR(100) NOT NULL, entity_id VARCHAR(100) NOT NULL, action VARCHAR(100) NOT NULL, before_state JSONB, after_state JSONB, ip_address VARCHAR(45), browser TEXT, request_id VARCHAR(120), created_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_actor_user_id ON audit_events (actor_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_entity_id ON audit_events (entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_entity_type ON audit_events (entity_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_action ON audit_events (action)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_request_id ON audit_events (request_id)")
    op.execute("CREATE TABLE IF NOT EXISTS login_sessions (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, refresh_token_id UUID REFERENCES refresh_tokens(id) ON DELETE SET NULL, ip_address VARCHAR(45), user_agent TEXT, browser VARCHAR(120), platform VARCHAR(120), status VARCHAR(40) NOT NULL, last_seen_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_login_sessions_user_id ON login_sessions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_login_sessions_status ON login_sessions (status)")
    op.execute("CREATE TABLE IF NOT EXISTS user_notes (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, author_user_id UUID REFERENCES users(id) ON DELETE SET NULL, body TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_notes_user_id ON user_notes (user_id)")
    op.execute("CREATE TABLE IF NOT EXISTS user_attachments (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, uploaded_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL, file_name VARCHAR(255) NOT NULL, file_url TEXT NOT NULL, content_type VARCHAR(120), created_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_attachments_user_id ON user_attachments (user_id)")
    op.execute("CREATE TABLE IF NOT EXISTS user_invitations (id UUID PRIMARY KEY, email VARCHAR(255) NOT NULL, invited_role_id UUID REFERENCES roles(id) ON DELETE SET NULL, organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL, department_id UUID REFERENCES departments(id) ON DELETE SET NULL, invited_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL, status VARCHAR(40) NOT NULL, token VARCHAR(120) NOT NULL UNIQUE, expires_at TIMESTAMPTZ, accepted_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_invitations_email ON user_invitations (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_invitations_status ON user_invitations (status)")
    op.execute("CREATE TABLE IF NOT EXISTS user_status_history (id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, previous_status VARCHAR(40), new_status VARCHAR(40) NOT NULL, reason TEXT, changed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL, created_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_status_history_user_id ON user_status_history (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_status_history_new_status ON user_status_history (new_status)")
    for role_name, description in ROLE_SEEDS:
        conn.execute(
            sa.text(
                "INSERT INTO roles (id, name, description, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :name, :description, now(), now()) "
                "ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, updated_at = now()"
            ),
            {"name": role_name, "description": description},
        )

    for key, module, label, description in PERMISSION_SEEDS:
        conn.execute(
            sa.text(
                "INSERT INTO permissions (id, key, module, label, description, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :key, :module, :label, :description, now(), now()) "
                "ON CONFLICT (key) DO UPDATE SET module = EXCLUDED.module, label = EXCLUDED.label, "
                "description = EXCLUDED.description, updated_at = now()"
            ),
            {
                "key": key,
                "module": module,
                "label": label,
                "description": description,
            },
        )

    for role_name, permission_keys in ROLE_PERMISSION_MAP.items():
        for permission_key in permission_keys:
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (id, role_id, permission_id, created_at) "
                    "SELECT gen_random_uuid(), r.id, p.id, now() "
                    "FROM roles r CROSS JOIN permissions p "
                    "WHERE r.name = :role_name AND p.key = :permission_key "
                    "AND NOT EXISTS ("
                    "SELECT 1 FROM role_permissions rp "
                    "WHERE rp.role_id = r.id AND rp.permission_id = p.id"
                    ")"
                ),
                {"role_name": role_name, "permission_key": permission_key},
            )

    conn.execute(
        sa.text(
            "INSERT INTO user_roles (id, user_id, role_id, assigned_by_user_id, is_primary, created_at) "
            "SELECT gen_random_uuid(), u.id, u.role_id, NULL, true, COALESCE(u.created_at, now()) "
            "FROM users u "
            "WHERE NOT EXISTS ("
            "SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = u.role_id"
            ")"
        )
    )

    conn.execute(
        sa.text(
            "INSERT INTO user_status_history (id, user_id, previous_status, new_status, reason, changed_by_user_id, created_at) "
            "SELECT gen_random_uuid(), u.id, NULL, COALESCE(u.status, 'ACTIVE'), 'Backfilled from existing user record', NULL, COALESCE(u.created_at, now()) "
            "FROM users u "
            "WHERE NOT EXISTS (SELECT 1 FROM user_status_history h WHERE h.user_id = u.id)"
        )
    )

    conn.execute(
        sa.text(
            "INSERT INTO organizations (id, name, industry, company_size, address, timezone_name, country, subscription_name, "
            "primary_contact_name, primary_contact_email, status, created_by_user_id, created_at, updated_at) "
            "SELECT gen_random_uuid(), company_name, COALESCE(industry, 'Healthcare'), "
            "CASE WHEN employees IS NULL THEN NULL ELSE employees::text || ' employees' END, "
            "location, 'Asia/Kolkata', 'India', 'Platform managed', "
            "TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')), email, "
            "CASE WHEN is_active THEN 'ACTIVE' ELSE 'INACTIVE' END, NULL, MIN(created_at), now() "
            "FROM users "
            "WHERE company_name IS NOT NULL AND company_name <> '' "
            "AND NOT EXISTS ("
            "SELECT 1 FROM organizations o WHERE o.name = users.company_name"
            ") "
            "GROUP BY company_name, industry, employees, location, first_name, last_name, email, is_active"
        )
    )

    conn.execute(
        sa.text(
            "INSERT INTO organization_memberships "
            "(id, user_id, organization_id, employee_id, package_name, status, is_verified, tags, created_by_user_id, joined_at, created_at, updated_at) "
            "SELECT gen_random_uuid(), u.id, o.id, NULL, NULL, COALESCE(u.status, 'ACTIVE'), u.is_verified, '[]'::jsonb, NULL, COALESCE(u.created_at, now()), COALESCE(u.created_at, now()), now() "
            "FROM users u "
            "JOIN organizations o ON o.name = u.company_name "
            "WHERE u.company_name IS NOT NULL AND u.company_name <> '' "
            "AND NOT EXISTS ("
            "SELECT 1 FROM organization_memberships om "
            "WHERE om.user_id = u.id AND om.organization_id = o.id"
            ")"
        )
    )


def _add_column_if_missing(conn: sa.Connection, table_name: str, column_name: str, column_sql: str) -> None:
    existing_columns = {column["name"] for column in sa.inspect(conn).get_columns(table_name)}
    if column_name not in existing_columns:
        op.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def downgrade() -> None:
    op.drop_index("ix_user_status_history_new_status", table_name="user_status_history")
    op.drop_index("ix_user_status_history_user_id", table_name="user_status_history")
    op.drop_table("user_status_history")

    op.drop_index("ix_user_invitations_status", table_name="user_invitations")
    op.drop_index("ix_user_invitations_email", table_name="user_invitations")
    op.drop_table("user_invitations")

    op.drop_index("ix_user_attachments_user_id", table_name="user_attachments")
    op.drop_table("user_attachments")

    op.drop_index("ix_user_notes_user_id", table_name="user_notes")
    op.drop_table("user_notes")

    op.drop_index("ix_login_sessions_status", table_name="login_sessions")
    op.drop_index("ix_login_sessions_user_id", table_name="login_sessions")
    op.drop_table("login_sessions")

    op.drop_index("ix_audit_events_request_id", table_name="audit_events")
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_type", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_organization_memberships_status", table_name="organization_memberships")
    op.drop_index("ix_organization_memberships_employee_id", table_name="organization_memberships")
    op.drop_table("organization_memberships")

    op.drop_table("departments")

    op.drop_index("ix_organizations_status", table_name="organizations")
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")

    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_index("ix_permissions_module", table_name="permissions")
    op.drop_index("ix_permissions_key", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_users_status", table_name="users")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "status")
    op.drop_column("users", "avatar_url")
