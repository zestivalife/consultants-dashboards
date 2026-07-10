"""expand people access with product scoped assignments

Revision ID: a8c4e2b7d901
Revises: f2b1c4d5e6f7
Create Date: 2026-07-10 18:40:00
"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision: str = "a8c4e2b7d901"
down_revision: Union[str, None] = "f2b1c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PRODUCT_ROWS = [
    {
        "id": uuid.UUID("10000000-0000-0000-0000-000000000001"),
        "key": "nuetra",
        "name": "Nuetra",
        "description": "Core adaptive nutrition and recovery platform",
        "status": "ACTIVE",
    },
    {
        "id": uuid.UUID("10000000-0000-0000-0000-000000000002"),
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


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_products_key", "products", ["key"], unique=True)
    op.create_index("ix_products_status", "products", ["status"], unique=False)

    op.add_column("organization_memberships", sa.Column("primary_product_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_organization_memberships_primary_product_id",
        "organization_memberships",
        "products",
        ["primary_product_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("audit_events", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_audit_events_product_id",
        "audit_events",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_audit_events_product_id", "audit_events", ["product_id"], unique=False)

    op.add_column("login_sessions", sa.Column("device_label", sa.String(length=160), nullable=True))
    op.add_column("user_attachments", sa.Column("attachment_type", sa.String(length=120), nullable=True))
    op.add_column("user_attachments", sa.Column("note", sa.Text(), nullable=True))

    op.add_column("user_invitations", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.add_column("user_invitations", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.add_column("user_invitations", sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_invitations", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_user_invitations_user_id",
        "user_invitations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_user_invitations_product_id",
        "user_invitations",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "organization_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "product_id", name="uq_organization_product"),
    )
    op.create_index("ix_organization_products_status", "organization_products", ["status"], unique=False)

    op.create_table(
        "user_product_access",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("role_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", "organization_id", name="uq_user_product_org_access"),
    )
    op.create_index("ix_user_product_access_status", "user_product_access", ["status"], unique=False)

    op.create_table(
        "package_catalog",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "code", name="uq_package_product_code"),
    )
    op.create_index("ix_package_catalog_code", "package_catalog", ["code"], unique=False)
    op.create_index("ix_package_catalog_status", "package_catalog", ["status"], unique=False)

    op.create_table(
        "service_catalog",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("provider_type", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "code", name="uq_service_product_code"),
    )
    op.create_index("ix_service_catalog_code", "service_catalog", ["code"], unique=False)
    op.create_index("ix_service_catalog_status", "service_catalog", ["status"], unique=False)

    op.create_table(
        "user_package_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["package_id"], ["package_catalog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_package_assignments_user_id", "user_package_assignments", ["user_id"], unique=False)

    op.create_table(
        "user_service_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["service_catalog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_service_assignments_user_id", "user_service_assignments", ["user_id"], unique=False)

    products_table = sa.table(
        "products",
        sa.column("id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    package_table = sa.table(
        "package_catalog",
        sa.column("id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("category", sa.String()),
        sa.column("status", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    service_table = sa.table(
        "service_catalog",
        sa.column("id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("category", sa.String()),
        sa.column("provider_type", sa.String()),
        sa.column("status", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(timezone.utc)
    op.bulk_insert(
        products_table,
        [
            {
                **row,
                "created_at": now,
                "updated_at": now,
            }
            for row in PRODUCT_ROWS
        ],
    )
    op.bulk_insert(
        package_table,
        [
            {
                "id": uuid.uuid4(),
                "product_id": product_id,
                "code": code,
                "name": name,
                "category": category,
                "status": "ACTIVE",
                "description": f"{name} package",
                "created_at": now,
                "updated_at": now,
            }
            for code, name, category, product_id in PACKAGE_ROWS
        ],
    )
    op.bulk_insert(
        service_table,
        [
            {
                "id": uuid.uuid4(),
                "product_id": product_id,
                "code": code,
                "name": name,
                "category": category,
                "provider_type": provider_type,
                "status": "ACTIVE",
                "description": f"{name} service",
                "created_at": now,
                "updated_at": now,
            }
            for code, name, category, provider_type, product_id in SERVICE_ROWS
        ],
    )

    op.execute(
        sa.text(
            """
            UPDATE organization_memberships
            SET primary_product_id = :product_id
            WHERE primary_product_id IS NULL
            """
        ).bindparams(product_id=PRODUCT_ROWS[0]["id"])
    )
    org_product_table = sa.table(
        "organization_products",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("product_id", sa.Uuid()),
        sa.column("status", sa.String()),
        sa.column("enabled_at", sa.DateTime(timezone=True)),
        sa.column("disabled_at", sa.DateTime(timezone=True)),
    )
    bind = op.get_bind()
    organization_ids = [row[0] for row in bind.execute(sa.text("SELECT id FROM organizations")).fetchall()]
    if organization_ids:
        op.bulk_insert(
            org_product_table,
            [
                {
                    "id": uuid.uuid4(),
                    "organization_id": organization_id,
                    "product_id": PRODUCT_ROWS[0]["id"],
                    "status": "ACTIVE",
                    "enabled_at": now,
                    "disabled_at": None,
                }
                for organization_id in organization_ids
            ],
        )


def downgrade() -> None:
    op.drop_index("ix_user_service_assignments_user_id", table_name="user_service_assignments")
    op.drop_table("user_service_assignments")
    op.drop_index("ix_user_package_assignments_user_id", table_name="user_package_assignments")
    op.drop_table("user_package_assignments")
    op.drop_index("ix_service_catalog_status", table_name="service_catalog")
    op.drop_index("ix_service_catalog_code", table_name="service_catalog")
    op.drop_table("service_catalog")
    op.drop_index("ix_package_catalog_status", table_name="package_catalog")
    op.drop_index("ix_package_catalog_code", table_name="package_catalog")
    op.drop_table("package_catalog")
    op.drop_index("ix_user_product_access_status", table_name="user_product_access")
    op.drop_table("user_product_access")
    op.drop_index("ix_organization_products_status", table_name="organization_products")
    op.drop_table("organization_products")
    op.drop_constraint("fk_user_invitations_product_id", "user_invitations", type_="foreignkey")
    op.drop_constraint("fk_user_invitations_user_id", "user_invitations", type_="foreignkey")
    op.drop_column("user_invitations", "cancelled_at")
    op.drop_column("user_invitations", "last_sent_at")
    op.drop_column("user_invitations", "product_id")
    op.drop_column("user_invitations", "user_id")
    op.drop_column("user_attachments", "note")
    op.drop_column("user_attachments", "attachment_type")
    op.drop_column("login_sessions", "device_label")
    op.drop_index("ix_audit_events_product_id", table_name="audit_events")
    op.drop_constraint("fk_audit_events_product_id", "audit_events", type_="foreignkey")
    op.drop_column("audit_events", "product_id")
    op.drop_constraint("fk_organization_memberships_primary_product_id", "organization_memberships", type_="foreignkey")
    op.drop_column("organization_memberships", "primary_product_id")
    op.drop_index("ix_products_status", table_name="products")
    op.drop_index("ix_products_key", table_name="products")
    op.drop_table("products")
