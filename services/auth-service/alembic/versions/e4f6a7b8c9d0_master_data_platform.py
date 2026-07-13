"""master data platform

Revision ID: e4f6a7b8c9d0
Revises: c9d0e1f2a3b4
Create Date: 2026-07-13 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f6a7b8c9d0"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = [
    ("master_data.read", "master_data", "View master data", "Read master data categories and values"),
    ("master_data.create", "master_data", "Create master data", "Create master data categories and values"),
    ("master_data.edit", "master_data", "Edit master data", "Update master data categories and values"),
    ("master_data.delete", "master_data", "Delete master data", "Soft delete master data categories and values"),
    ("master_data.restore", "master_data", "Restore master data", "Restore soft-deleted master data"),
    ("master_data.import", "master_data", "Import master data", "Bulk import master data values"),
    ("master_data.export", "master_data", "Export master data", "Export master data values"),
]

CATEGORIES = [
    ("GLOBAL", "industries", "Industries", "Industries supported by Zestiva enterprise customers", 10),
    ("GLOBAL", "company_sizes", "Company Sizes", "Employee count bands for organization setup", 20),
    ("GLOBAL", "countries", "Countries", "Supported countries for platform operations", 30),
    ("GLOBAL", "timezones", "Timezones", "Supported workspace timezones", 40),
    ("GLOBAL", "wellness_goals", "Wellness Goals", "Reusable wellness goal taxonomy across products", 50),
    ("GLOBAL", "package_types", "Package Types", "Reusable package type taxonomy", 60),
    ("GLOBAL", "service_categories", "Service Categories", "Reusable service category taxonomy", 70),
    ("GLOBAL", "provider_types", "Provider Types", "Practitioner, mentor, consultant, and AI provider taxonomy", 80),
]

ITEMS = [
    ("industries", "healthcare", "Healthcare", "Hospitals, clinics, diagnostics, and health operations", 10),
    ("industries", "technology", "Technology", "Software, SaaS, IT services, and product companies", 20),
    ("industries", "manufacturing", "Manufacturing", "Factories, industrial operations, and supply chains", 30),
    ("industries", "education", "Education", "Schools, universities, and learning organizations", 40),
    ("company_sizes", "1-50", "1-50 employees", "Small teams and startups", 10),
    ("company_sizes", "51-200", "51-200 employees", "Growing organizations", 20),
    ("company_sizes", "201-1000", "201-1000 employees", "Mid-market organizations", 30),
    ("company_sizes", "1000-plus", "1000+ employees", "Enterprise organizations", 40),
    ("countries", "IN", "India", "India", 10),
    ("countries", "US", "United States", "United States", 20),
    ("timezones", "Asia/Kolkata", "Asia/Kolkata", "India Standard Time", 10),
    ("timezones", "UTC", "UTC", "Coordinated Universal Time", 20),
    ("wellness_goals", "better_energy", "Better Energy", "Improve daily energy and fatigue resilience", 10),
    ("wellness_goals", "better_sleep", "Better Sleep", "Improve sleep quality and recovery", 20),
    ("wellness_goals", "weight_loss", "Weight Loss", "Support healthy fat loss and metabolic balance", 30),
    ("wellness_goals", "sugar_control", "Sugar Control", "Improve glucose and insulin-related markers", 40),
    ("wellness_goals", "hormone_balance", "Hormone Balance", "Support hormone health and cycle-related goals", 50),
    ("package_types", "nuetra", "Nuetra", "Nuetra product packages", 10),
    ("package_types", "fiteatsy", "FitEatsy", "FitEatsy product packages", 20),
    ("package_types", "corporate", "Corporate", "Corporate wellness packages", 30),
    ("package_types", "retail", "Retail", "Direct-to-consumer packages", 40),
    ("service_categories", "nutrition", "Nutrition", "Diet, meal, and nutrition planning services", 10),
    ("service_categories", "consultation", "Consultation", "Human consultation and review services", 20),
    ("service_categories", "recovery", "Recovery", "Recovery and lifestyle behavior services", 30),
    ("service_categories", "assessment", "Assessment", "Questionnaire, biomarker, and diagnostic assessments", 40),
    ("service_categories", "ai", "AI", "AI-assisted platform services", 50),
    ("provider_types", "practitioner", "Practitioner", "Licensed or qualified practitioner", 10),
    ("provider_types", "mentor", "Mentor", "Lifestyle and adherence mentor", 20),
    ("provider_types", "consultant", "Consultant", "Nutrition or wellness consultant", 30),
    ("provider_types", "ai", "AI", "AI-assisted provider", 40),
]


def upgrade() -> None:
    op.create_table(
        "master_data_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False, server_default="GLOBAL"),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_schema", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope", "key", name="uq_master_data_category_scope_key"),
    )
    op.create_index("ix_master_data_categories_scope", "master_data_categories", ["scope"])
    op.create_index("ix_master_data_categories_key", "master_data_categories", ["key"])
    op.create_index("ix_master_data_categories_status", "master_data_categories", ["status"])
    op.create_index("ix_master_data_categories_deleted_at", "master_data_categories", ["deleted_at"])

    op.create_table(
        "master_data_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["master_data_categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "code", name="uq_master_data_item_category_code"),
    )
    op.create_index("ix_master_data_items_category_id", "master_data_items", ["category_id"])
    op.create_index("ix_master_data_items_product_id", "master_data_items", ["product_id"])
    op.create_index("ix_master_data_items_organization_id", "master_data_items", ["organization_id"])
    op.create_index("ix_master_data_items_code", "master_data_items", ["code"])
    op.create_index("ix_master_data_items_label", "master_data_items", ["label"])
    op.create_index("ix_master_data_items_status", "master_data_items", ["status"])
    op.create_index("ix_master_data_items_deleted_at", "master_data_items", ["deleted_at"])

    conn = op.get_bind()
    for key, module, label, description in PERMISSIONS:
        conn.execute(
            sa.text(
                "INSERT INTO permissions (id, key, module, label, description, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :key, :module, :label, :description, now(), now()) "
                "ON CONFLICT (key) DO UPDATE SET module = EXCLUDED.module, label = EXCLUDED.label, "
                "description = EXCLUDED.description, updated_at = now()"
            ),
            {"key": key, "module": module, "label": label, "description": description},
        )

    for role_name in ("platform_owner", "superuser"):
        for permission_key, *_ in PERMISSIONS:
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (id, role_id, permission_id, created_at) "
                    "SELECT gen_random_uuid(), r.id, p.id, now() FROM roles r CROSS JOIN permissions p "
                    "WHERE r.name = :role_name AND p.key = :permission_key "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ),
                {"role_name": role_name, "permission_key": permission_key},
            )

    for scope, key, name, description, sort_order in CATEGORIES:
        conn.execute(
            sa.text(
                "INSERT INTO master_data_categories (id, scope, key, name, description, status, is_system, sort_order, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :scope, :key, :name, :description, 'ACTIVE', true, :sort_order, now(), now()) "
                "ON CONFLICT (scope, key) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, "
                "sort_order = EXCLUDED.sort_order, updated_at = now(), deleted_at = NULL, status = 'ACTIVE'"
            ),
            {"scope": scope, "key": key, "name": name, "description": description, "sort_order": sort_order},
        )

    for category_key, code, label, description, sort_order in ITEMS:
        conn.execute(
            sa.text(
                "INSERT INTO master_data_items (id, category_id, code, label, description, status, sort_order, created_at, updated_at) "
                "SELECT gen_random_uuid(), c.id, :code, :label, :description, 'ACTIVE', :sort_order, now(), now() "
                "FROM master_data_categories c WHERE c.scope = 'GLOBAL' AND c.key = :category_key "
                "ON CONFLICT (category_id, code) DO UPDATE SET label = EXCLUDED.label, description = EXCLUDED.description, "
                "sort_order = EXCLUDED.sort_order, updated_at = now(), deleted_at = NULL, status = 'ACTIVE'"
            ),
            {"category_key": category_key, "code": code, "label": label, "description": description, "sort_order": sort_order},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for permission_key, *_ in PERMISSIONS:
        conn.execute(
            sa.text(
                "DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE key = :permission_key)"
            ),
            {"permission_key": permission_key},
        )
        conn.execute(sa.text("DELETE FROM permissions WHERE key = :permission_key"), {"permission_key": permission_key})

    op.drop_index("ix_master_data_items_deleted_at", table_name="master_data_items")
    op.drop_index("ix_master_data_items_status", table_name="master_data_items")
    op.drop_index("ix_master_data_items_label", table_name="master_data_items")
    op.drop_index("ix_master_data_items_code", table_name="master_data_items")
    op.drop_index("ix_master_data_items_organization_id", table_name="master_data_items")
    op.drop_index("ix_master_data_items_product_id", table_name="master_data_items")
    op.drop_index("ix_master_data_items_category_id", table_name="master_data_items")
    op.drop_table("master_data_items")
    op.drop_index("ix_master_data_categories_deleted_at", table_name="master_data_categories")
    op.drop_index("ix_master_data_categories_status", table_name="master_data_categories")
    op.drop_index("ix_master_data_categories_key", table_name="master_data_categories")
    op.drop_index("ix_master_data_categories_scope", table_name="master_data_categories")
    op.drop_table("master_data_categories")
