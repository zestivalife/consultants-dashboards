from __future__ import annotations

import asyncio
import os

import asyncpg


TARGET_ALEMBIC_REVISION = "d3e4f5a6b7c8"

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
    "corporate_admin": [
        "users.read",
        "users.create",
        "users.edit",
        "users.invite",
        "users.export",
        "reports.view",
        "organizations.manage",
    ],
    "practitioner": ["users.read", "reports.view"],
    "mentor": ["users.read", "reports.view"],
    "consultant": ["users.read", "reports.view"],
    "senior_consultant": ["users.read", "reports.view", "users.export"],
    "employee": [],
}

PRODUCT_ROWS = [
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "key": "nuetra",
        "name": "Nuetra",
        "description": "Core adaptive nutrition and recovery platform",
        "status": "ACTIVE",
    },
    {
        "id": "10000000-0000-0000-0000-000000000002",
        "key": "fiteatsy",
        "name": "FitEatsy",
        "description": "Nutrition and habit product line for lifestyle recovery programs",
        "status": "ACTIVE",
    },
]

PACKAGE_ROWS = [
    ("nuetra-enterprise-recovery", "Enterprise Recovery", "Corporate", PRODUCT_ROWS[0]["id"]),
    ("nuetra-adaptive-nutrition", "Adaptive Nutrition", "Corporate", PRODUCT_ROWS[0]["id"]),
    ("nuetra-performance-plus", "Performance Plus", "Retail", PRODUCT_ROWS[0]["id"]),
    ("fiteatsy-transform", "Transform 12 Week", "FitEatsy", PRODUCT_ROWS[1]["id"]),
    ("fiteatsy-sugar-balance", "Sugar Balance", "FitEatsy", PRODUCT_ROWS[1]["id"]),
    ("fiteatsy-hormone-reset", "Hormone Reset", "FitEatsy", PRODUCT_ROWS[1]["id"]),
]

SERVICE_ROWS = [
    ("nuetra-assessment", "Assessment Review", "Assessment", "consultant", PRODUCT_ROWS[0]["id"]),
    ("nuetra-recovery", "Recovery Coaching", "Recovery", "mentor", PRODUCT_ROWS[0]["id"]),
    ("nuetra-meal-plan", "Meal Plan Personalization", "Nutrition", "practitioner", PRODUCT_ROWS[0]["id"]),
    ("fiteatsy-meal-plan", "FitEatsy Meal Plan", "Nutrition", "consultant", PRODUCT_ROWS[1]["id"]),
    ("fiteatsy-chat", "Coach Chat", "Consultation", "consultant", PRODUCT_ROWS[1]["id"]),
    ("fiteatsy-habit-review", "Habit Review", "AI", "mentor", PRODUCT_ROWS[1]["id"]),
]


def _database_url() -> str:
    url = os.environ["DATABASE_URL"]
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _execute(conn: asyncpg.Connection, statement: str) -> None:
    await conn.execute(statement)


async def _add_columns(conn: asyncpg.Connection, table: str, columns: dict[str, str]) -> None:
    for column_name, column_sql in columns.items():
        await _execute(conn, f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {column_sql}")


async def reconcile() -> None:
    conn = await asyncpg.connect(_database_url())
    try:
        await _execute(conn, "CREATE EXTENSION IF NOT EXISTS pgcrypto")

        user_columns = {
            "company_name": "VARCHAR(255)",
            "location": "VARCHAR(255)",
            "employees": "INTEGER",
            "industry": "VARCHAR(255)",
            "first_name": "VARCHAR(100)",
            "last_name": "VARCHAR(100)",
            "phone": "VARCHAR(20)",
            "mobile": "VARCHAR(20)",
            "avatar_url": "VARCHAR(500)",
            "status": "VARCHAR(40) NOT NULL DEFAULT 'ACTIVE'",
            "permissions": "JSON NOT NULL DEFAULT '[]'::json",
            "company_id": "UUID",
            "last_login_at": "TIMESTAMPTZ",
            "last_login": "TIMESTAMPTZ",
            "deleted_at": "TIMESTAMPTZ",
            "email_verified": "BOOLEAN NOT NULL DEFAULT false",
            "mobile_verified": "BOOLEAN NOT NULL DEFAULT false",
            "remember_me": "BOOLEAN NOT NULL DEFAULT false",
            "password_changed_at": "TIMESTAMPTZ",
            "mfa_enabled": "BOOLEAN NOT NULL DEFAULT false",
            "current_session_version": "INTEGER NOT NULL DEFAULT 1",
            "refresh_token_version": "INTEGER NOT NULL DEFAULT 1",
            "is_active": "BOOLEAN NOT NULL DEFAULT true",
        }
        await _add_columns(conn, "users", user_columns)
        await _execute(conn, "UPDATE users SET email_verified = is_verified WHERE email_verified = false")
        await _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_mobile ON users (mobile) WHERE mobile IS NOT NULL")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_users_status ON users (status)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(255) NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS permissions (
                id UUID PRIMARY KEY,
                key VARCHAR(120) NOT NULL UNIQUE,
                module VARCHAR(80) NOT NULL,
                label VARCHAR(120) NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_permissions_key ON permissions (key)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_permissions_module ON permissions (module)")
        for key, module, label, description in PERMISSION_SEEDS:
            await conn.execute(
                """
                INSERT INTO permissions (id, key, module, label, description, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, now(), now())
                ON CONFLICT (key) DO UPDATE
                SET module = EXCLUDED.module,
                    label = EXCLUDED.label,
                    description = EXCLUDED.description,
                    updated_at = now()
                """,
                key,
                module,
                label,
                description,
            )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                id UUID PRIMARY KEY,
                role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_role_permission ON role_permissions (role_id, permission_id)",
        )
        for role_name, description in ROLE_SEEDS:
            await conn.execute(
                """
                INSERT INTO roles (id, name, description, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, now(), now())
                ON CONFLICT (name) DO UPDATE
                SET description = EXCLUDED.description,
                    updated_at = now()
                """,
                role_name,
                description,
            )
        for role_name, permission_keys in ROLE_PERMISSION_MAP.items():
            for permission_key in permission_keys:
                await conn.execute(
                    """
                    INSERT INTO role_permissions (id, role_id, permission_id, created_at)
                    SELECT gen_random_uuid(), r.id, p.id, now()
                    FROM roles r
                    CROSS JOIN permissions p
                    WHERE r.name = $1
                      AND p.key = $2
                      AND NOT EXISTS (
                        SELECT 1
                        FROM role_permissions rp
                        WHERE rp.role_id = r.id
                          AND rp.permission_id = p.id
                      )
                    """,
                    role_name,
                    permission_key,
                )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_roles (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                is_primary BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_role ON user_roles (user_id, role_id)")
        await _execute(
            conn,
            """
            INSERT INTO user_roles (id, user_id, role_id, assigned_by_user_id, is_primary, created_at)
            SELECT gen_random_uuid(), u.id, u.role_id, NULL, true, COALESCE(u.created_at, now())
            FROM users u
            WHERE u.role_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1
                FROM user_roles ur
                WHERE ur.user_id = u.id
                  AND ur.role_id = u.role_id
              )
            """,
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS auth_audit_logs (
                id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                event_type VARCHAR(100) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN NOT NULL DEFAULT false,
                details JSON DEFAULT '{}'::json,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_user_id ON auth_audit_logs (user_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_event_type ON auth_audit_logs (event_type)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_auth_audit_logs_created_at ON auth_audit_logs (created_at)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id UUID PRIMARY KEY,
                actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                entity_type VARCHAR(100) NOT NULL,
                entity_id VARCHAR(100) NOT NULL,
                action VARCHAR(100) NOT NULL,
                product_id UUID,
                before_state JSONB,
                after_state JSONB,
                ip_address VARCHAR(45),
                browser TEXT,
                request_id VARCHAR(120),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _add_columns(conn, "audit_events", {"product_id": "UUID"})
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_actor_user_id ON audit_events (actor_user_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_entity_id ON audit_events (entity_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_entity_type ON audit_events (entity_type)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_action ON audit_events (action)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_product_id ON audit_events (product_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events (created_at)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_audit_events_request_id ON audit_events (request_id)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS login_sessions (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                refresh_token_id UUID REFERENCES refresh_tokens(id) ON DELETE SET NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                browser VARCHAR(120),
                platform VARCHAR(120),
                device_label VARCHAR(160),
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                revoked_at TIMESTAMPTZ
            )
            """,
        )
        await _execute(conn, "ALTER TABLE login_sessions ADD COLUMN IF NOT EXISTS device_label VARCHAR(160)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_login_sessions_user_id ON login_sessions (user_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_login_sessions_status ON login_sessions (status)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _add_columns(
            conn,
            "organizations",
            {
                "logo_url": "TEXT",
                "industry": "VARCHAR(255)",
                "company_size": "VARCHAR(80)",
                "gst_number": "VARCHAR(50)",
                "address": "TEXT",
                "timezone_name": "VARCHAR(80)",
                "country": "VARCHAR(100)",
                "subscription_name": "VARCHAR(255)",
                "renewal_date": "DATE",
                "primary_contact_name": "VARCHAR(255)",
                "primary_contact_email": "VARCHAR(255)",
                "created_by_user_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
                "deactivated_at": "TIMESTAMPTZ",
            },
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations (name)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_organizations_status ON organizations (status)")
        await _execute(
            conn,
            """
            INSERT INTO organizations (
                id, name, industry, company_size, address, timezone_name, country,
                subscription_name, primary_contact_name, primary_contact_email,
                status, created_by_user_id, created_at, updated_at
            )
            SELECT gen_random_uuid(),
                   company_name,
                   COALESCE(industry, 'Healthcare'),
                   CASE WHEN employees IS NULL THEN NULL ELSE employees::text || ' employees' END,
                   location,
                   'Asia/Kolkata',
                   'India',
                   'Platform managed',
                   TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')),
                   email,
                   CASE WHEN is_active THEN 'ACTIVE' ELSE 'INACTIVE' END,
                   NULL,
                   MIN(COALESCE(created_at, now())),
                   now()
            FROM users
            WHERE company_name IS NOT NULL
              AND company_name <> ''
              AND NOT EXISTS (
                SELECT 1
                FROM organizations o
                WHERE o.name = users.company_name
              )
            GROUP BY company_name, industry, employees, location, first_name, last_name, email, is_active
            """,
        )
        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS departments (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_department_org_name ON departments (organization_id, name)",
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS organization_memberships (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
                employee_id VARCHAR(80),
                package_name VARCHAR(255),
                assigned_practitioner_id UUID REFERENCES users(id) ON DELETE SET NULL,
                assigned_mentor_id UUID REFERENCES users(id) ON DELETE SET NULL,
                assigned_consultant_id UUID REFERENCES users(id) ON DELETE SET NULL,
                primary_product_id UUID,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                is_verified BOOLEAN NOT NULL DEFAULT false,
                tags JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                deactivated_at TIMESTAMPTZ
            )
            """,
        )
        await _add_columns(
            conn,
            "organization_memberships",
            {
                "primary_product_id": "UUID",
                "assigned_practitioner_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
                "assigned_mentor_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
                "assigned_consultant_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
                "created_by_user_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
                "tags": "JSONB NOT NULL DEFAULT '[]'::jsonb",
                "deactivated_at": "TIMESTAMPTZ",
            },
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_organization_membership ON organization_memberships (user_id, organization_id)",
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_organization_memberships_employee_id ON organization_memberships (employee_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_organization_memberships_status ON organization_memberships (status)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY,
                key VARCHAR(80) NOT NULL UNIQUE,
                name VARCHAR(120) NOT NULL UNIQUE,
                description TEXT,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            """
            INSERT INTO products (id, key, name, description, status, created_at, updated_at)
            VALUES
                ('10000000-0000-0000-0000-000000000001', 'nuetra', 'Nuetra', 'Core adaptive nutrition and recovery platform', 'ACTIVE', now(), now()),
                ('10000000-0000-0000-0000-000000000002', 'fiteatsy', 'FitEatsy', 'Nutrition and habit product line for lifestyle recovery programs', 'ACTIVE', now(), now())
            ON CONFLICT (key) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, status = EXCLUDED.status, updated_at = now()
            """,
        )
        await _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS ix_products_key ON products (key)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_products_status ON products (status)")
        await _execute(conn, "UPDATE organization_memberships SET primary_product_id = '10000000-0000-0000-0000-000000000001' WHERE primary_product_id IS NULL")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS organization_products (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                enabled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                disabled_at TIMESTAMPTZ
            )
            """,
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_organization_product ON organization_products (organization_id, product_id)",
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_organization_products_status ON organization_products (status)")
        await _execute(
            conn,
            """
            INSERT INTO organization_products (id, organization_id, product_id, status, enabled_at, disabled_at)
            SELECT gen_random_uuid(), o.id, p.id, 'ACTIVE', now(), NULL
            FROM organizations o
            CROSS JOIN products p
            WHERE p.key IN ('nuetra', 'fiteatsy')
              AND NOT EXISTS (
                SELECT 1
                FROM organization_products op
                WHERE op.organization_id = o.id
                  AND op.product_id = p.id
              )
            """,
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS package_catalog (
                id UUID PRIMARY KEY,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                code VARCHAR(100) NOT NULL,
                name VARCHAR(160) NOT NULL,
                category VARCHAR(120),
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_package_product_code ON package_catalog (product_id, code)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_package_catalog_code ON package_catalog (code)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_package_catalog_status ON package_catalog (status)")
        for code, name, category, product_id in PACKAGE_ROWS:
            await conn.execute(
                """
                INSERT INTO package_catalog (id, product_id, code, name, category, status, description, created_at, updated_at)
                VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, 'ACTIVE', $5, now(), now())
                ON CONFLICT (product_id, code) DO UPDATE
                SET name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    status = EXCLUDED.status,
                    description = EXCLUDED.description,
                    updated_at = now()
                """,
                product_id,
                code,
                name,
                category,
                f"{name} package",
            )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS service_catalog (
                id UUID PRIMARY KEY,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                code VARCHAR(100) NOT NULL,
                name VARCHAR(160) NOT NULL,
                category VARCHAR(120),
                provider_type VARCHAR(120),
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_service_product_code ON service_catalog (product_id, code)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_service_catalog_code ON service_catalog (code)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_service_catalog_status ON service_catalog (status)")
        for code, name, category, provider_type, product_id in SERVICE_ROWS:
            await conn.execute(
                """
                INSERT INTO service_catalog (id, product_id, code, name, category, provider_type, status, description, created_at, updated_at)
                VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, $5, 'ACTIVE', $6, now(), now())
                ON CONFLICT (product_id, code) DO UPDATE
                SET name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    provider_type = EXCLUDED.provider_type,
                    status = EXCLUDED.status,
                    description = EXCLUDED.description,
                    updated_at = now()
                """,
                product_id,
                code,
                name,
                category,
                provider_type,
                f"{name} service",
            )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_product_access (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
                role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                is_primary BOOLEAN NOT NULL DEFAULT false,
                permissions JSON NOT NULL DEFAULT '[]'::json,
                assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_product_org_access ON user_product_access (user_id, product_id, organization_id)",
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_package_assignments (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                package_id UUID NOT NULL REFERENCES package_catalog(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                notes TEXT,
                assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                ended_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_package_assignments_user_id ON user_package_assignments (user_id)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_service_assignments (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                service_id UUID NOT NULL REFERENCES service_catalog(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
                product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                status VARCHAR(40) NOT NULL DEFAULT 'ACTIVE',
                notes TEXT,
                assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                ended_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_service_assignments_user_id ON user_service_assignments (user_id)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_notes (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                author_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_notes_user_id ON user_notes (user_id)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_attachments (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                uploaded_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                file_name VARCHAR(255) NOT NULL,
                file_url TEXT NOT NULL,
                content_type VARCHAR(120),
                attachment_type VARCHAR(120),
                note TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _add_columns(
            conn,
            "user_attachments",
            {
                "attachment_type": "VARCHAR(120)",
                "note": "TEXT",
            },
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_attachments_user_id ON user_attachments (user_id)")

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_status_history (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                previous_status VARCHAR(40),
                new_status VARCHAR(40) NOT NULL,
                reason TEXT,
                changed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_status_history_user_id ON user_status_history (user_id)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_status_history_new_status ON user_status_history (new_status)")
        await _execute(
            conn,
            """
            INSERT INTO user_status_history (id, user_id, previous_status, new_status, reason, changed_by_user_id, created_at)
            SELECT gen_random_uuid(), u.id, NULL, COALESCE(u.status, 'ACTIVE'), 'Backfilled during auth schema reconciliation', NULL, COALESCE(u.created_at, now())
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1
                FROM user_status_history h
                WHERE h.user_id = u.id
            )
            """,
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS user_invitations (
                id UUID PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                invited_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
                organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
                invited_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                product_id UUID REFERENCES products(id) ON DELETE SET NULL,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
                token VARCHAR(120) NOT NULL DEFAULT '',
                token_hash VARCHAR(64),
                token_fingerprint VARCHAR(16),
                expires_at TIMESTAMPTZ,
                accepted_at TIMESTAMPTZ,
                last_sent_at TIMESTAMPTZ,
                cancelled_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )
        invitation_columns = {
            "first_name": "VARCHAR(120)",
            "last_name": "VARCHAR(120)",
            "mobile_number": "VARCHAR(40)",
            "country_code": "VARCHAR(8)",
            "user_id": "UUID REFERENCES users(id) ON DELETE SET NULL",
            "product_id": "UUID REFERENCES products(id) ON DELETE SET NULL",
            "department_id": "UUID REFERENCES departments(id) ON DELETE SET NULL",
            "token_hash": "VARCHAR(64)",
            "token_fingerprint": "VARCHAR(16)",
            "last_sent_at": "TIMESTAMPTZ",
            "cancelled_at": "TIMESTAMPTZ",
            "updated_at": "TIMESTAMPTZ NOT NULL DEFAULT now()",
        }
        for column_name, column_sql in invitation_columns.items():
            await _execute(conn, f"ALTER TABLE user_invitations ADD COLUMN IF NOT EXISTS {column_name} {column_sql}")
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token_hash = encode(digest(NULLIF(token, ''), 'sha256'), 'hex')
            WHERE token_hash IS NULL AND NULLIF(token, '') IS NOT NULL
            """,
        )
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token = 'redacted:' || id::text
            WHERE token_hash IS NOT NULL AND token NOT LIKE 'redacted:%'
            """,
        )
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token_fingerprint = substring(token_hash from 1 for 12)
            WHERE token_hash IS NOT NULL AND token_fingerprint IS NULL
            """,
        )
        await _execute(
            conn,
            """
            UPDATE user_invitations
            SET token_hash = encode(digest(id::text || ':' || email, 'sha256'), 'hex'),
                token = 'redacted:' || id::text,
                token_fingerprint = substring(encode(digest(id::text || ':' || email, 'sha256'), 'hex') from 1 for 12)
            WHERE token_hash IS NULL
            """
        )
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_invitations_email ON user_invitations (email)")
        await _execute(conn, "CREATE INDEX IF NOT EXISTS ix_user_invitations_status ON user_invitations (status)")
        await _execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_invitations_token_hash ON user_invitations (token_hash)",
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS invitation_email_outbox (
                id UUID PRIMARY KEY,
                invitation_id UUID REFERENCES user_invitations(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                event_type VARCHAR(80) NOT NULL,
                status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
                payload JSON NOT NULL DEFAULT '{}'::json,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )

        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS password_history (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
        )

        await _execute(conn, "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
        current = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        if current:
            await conn.execute("UPDATE alembic_version SET version_num = $1", TARGET_ALEMBIC_REVISION)
        else:
            await conn.execute("INSERT INTO alembic_version (version_num) VALUES ($1)", TARGET_ALEMBIC_REVISION)
        print(f"Auth schema reconciled and stamped at {TARGET_ALEMBIC_REVISION}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(reconcile())
