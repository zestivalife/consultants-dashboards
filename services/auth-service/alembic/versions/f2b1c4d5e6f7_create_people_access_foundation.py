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
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))
    op.add_column(
        "users",
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
    )
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_status", "users", ["status"], unique=False)
    op.alter_column("users", "status", server_default=None)

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("module", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_permissions_key", "permissions", ["key"], unique=True)
    op.create_index("ix_permissions_module", "permissions", ["module"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("company_size", sa.String(length=80), nullable=True),
        sa.Column("gst_number", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("timezone_name", sa.String(length=80), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("subscription_name", sa.String(length=255), nullable=True),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("primary_contact_name", sa.String(length=255), nullable=True),
        sa.Column("primary_contact_email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=True)
    op.create_index("ix_organizations_status", "organizations", ["status"], unique=False)

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_department_org_name"),
    )

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("employee_id", sa.String(length=80), nullable=True),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("assigned_practitioner_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_mentor_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_consultant_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_consultant_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_mentor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_practitioner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_user_organization_membership"),
    )
    op.create_index("ix_organization_memberships_employee_id", "organization_memberships", ["employee_id"], unique=False)
    op.create_index("ix_organization_memberships_status", "organization_memberships", ["status"], unique=False)
    op.alter_column("organization_memberships", "tags", server_default=None)
    op.alter_column("organization_memberships", "is_verified", server_default=None)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("browser", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"], unique=False)
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"], unique=False)
    op.create_index("ix_audit_events_action", "audit_events", ["action"], unique=False)
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"], unique=False)
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"], unique=False)

    op.create_table(
        "login_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_id", sa.Uuid(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("browser", sa.String(length=120), nullable=True),
        sa.Column("platform", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["refresh_token_id"], ["refresh_tokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_login_sessions_user_id", "login_sessions", ["user_id"], unique=False)
    op.create_index("ix_login_sessions_status", "login_sessions", ["status"], unique=False)

    op.create_table(
        "user_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_notes_user_id", "user_notes", ["user_id"], unique=False)

    op.create_table(
        "user_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_attachments_user_id", "user_attachments", ["user_id"], unique=False)

    op.create_table(
        "user_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("invited_role_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("invited_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invited_role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_user_invitations_email", "user_invitations", ["email"], unique=False)
    op.create_index("ix_user_invitations_status", "user_invitations", ["status"], unique=False)

    op.create_table(
        "user_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("previous_status", sa.String(length=40), nullable=True),
        sa.Column("new_status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_status_history_user_id", "user_status_history", ["user_id"], unique=False)
    op.create_index("ix_user_status_history_new_status", "user_status_history", ["new_status"], unique=False)

    conn = op.get_bind()
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
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ),
                {"role_name": role_name, "permission_key": permission_key},
            )

    conn.execute(
        sa.text(
            "INSERT INTO user_roles (id, user_id, role_id, assigned_by_user_id, is_primary, created_at) "
            "SELECT gen_random_uuid(), u.id, u.role_id, NULL, true, COALESCE(u.created_at, now()) "
            "FROM users u "
            "ON CONFLICT (user_id, role_id) DO NOTHING"
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
            "GROUP BY company_name, industry, employees, location, first_name, last_name, email, is_active "
            "ON CONFLICT (name) DO NOTHING"
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
            "ON CONFLICT (user_id, organization_id) DO NOTHING"
        )
    )


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
