"""identity onboarding foundation

Revision ID: c9d0e1f2a3b4
Revises: b7d9e3f1a204
Create Date: 2026-07-13 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b7d9e3f1a204"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("mobile", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("mobile_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("remember_me", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("last_login", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("current_session_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("users", sa.Column("refresh_token_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_unique_constraint("uq_users_mobile", "users", ["mobile"])
    op.execute("UPDATE users SET email_verified = is_verified WHERE email_verified = false")

    _create_role_profile_table("practitioner_profiles")
    _create_role_profile_table("mentor_profiles", extra_columns=[
        sa.Column("program_focus", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("availability", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    ])
    _create_role_profile_table("consultant_profiles", extra_columns=[
        sa.Column("seniority", sa.String(length=80), nullable=True),
        sa.Column("availability", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    ])
    _create_role_profile_table("organization_admin_profiles", extra_columns=[
        sa.Column("organization_scope", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    ])
    _create_role_profile_table("corporate_admin_profiles", extra_columns=[
        sa.Column("company_scope", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    ])

    op.create_table(
        "onboarding_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("documents", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("agreements", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("approval_steps", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("profile_sections", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "product_id", "version", name="uq_onboarding_template_scope"),
    )
    op.create_index("ix_onboarding_templates_role_id", "onboarding_templates", ["role_id"])
    op.create_index("ix_onboarding_templates_product_id", "onboarding_templates", ["product_id"])
    op.create_index("ix_onboarding_templates_status", "onboarding_templates", ["status"])

    op.create_table(
        "onboarding_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=True),
        sa.Column("invitation_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="INVITED"),
        sa.Column("current_step_key", sa.String(length=120), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invitation_id"], ["user_invitations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["onboarding_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_onboarding_instances_user_id", "onboarding_instances", ["user_id"])
    op.create_index("ix_onboarding_instances_status", "onboarding_instances", ["status"])

    op.create_table(
        "onboarding_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instance_id", sa.Uuid(), nullable=False),
        sa.Column("step_key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="PENDING"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["onboarding_instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "step_key", name="uq_onboarding_instance_step"),
    )
    op.create_index("ix_onboarding_steps_instance_id", "onboarding_steps", ["instance_id"])
    op.create_index("ix_onboarding_steps_status", "onboarding_steps", ["status"])

    op.create_table(
        "onboarding_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instance_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("document_type", sa.String(length=120), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="UPLOADED"),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["instance_id"], ["onboarding_instances.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_onboarding_documents_instance_id", "onboarding_documents", ["instance_id"])
    op.create_index("ix_onboarding_documents_document_type", "onboarding_documents", ["document_type"])
    op.create_index("ix_onboarding_documents_status", "onboarding_documents", ["status"])

    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("assigned_to_user_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="PENDING"),
        sa.Column("decision", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_workflows_entity_type", "approval_workflows", ["entity_type"])
    op.create_index("ix_approval_workflows_entity_id", "approval_workflows", ["entity_id"])
    op.create_index("ix_approval_workflows_status", "approval_workflows", ["status"])


def downgrade() -> None:
    op.drop_index("ix_approval_workflows_status", table_name="approval_workflows")
    op.drop_index("ix_approval_workflows_entity_id", table_name="approval_workflows")
    op.drop_index("ix_approval_workflows_entity_type", table_name="approval_workflows")
    op.drop_table("approval_workflows")
    op.drop_index("ix_onboarding_documents_status", table_name="onboarding_documents")
    op.drop_index("ix_onboarding_documents_document_type", table_name="onboarding_documents")
    op.drop_index("ix_onboarding_documents_instance_id", table_name="onboarding_documents")
    op.drop_table("onboarding_documents")
    op.drop_index("ix_onboarding_steps_status", table_name="onboarding_steps")
    op.drop_index("ix_onboarding_steps_instance_id", table_name="onboarding_steps")
    op.drop_table("onboarding_steps")
    op.drop_index("ix_onboarding_instances_status", table_name="onboarding_instances")
    op.drop_index("ix_onboarding_instances_user_id", table_name="onboarding_instances")
    op.drop_table("onboarding_instances")
    op.drop_index("ix_onboarding_templates_status", table_name="onboarding_templates")
    op.drop_index("ix_onboarding_templates_product_id", table_name="onboarding_templates")
    op.drop_index("ix_onboarding_templates_role_id", table_name="onboarding_templates")
    op.drop_table("onboarding_templates")

    for table_name in [
        "corporate_admin_profiles",
        "organization_admin_profiles",
        "consultant_profiles",
        "mentor_profiles",
        "practitioner_profiles",
    ]:
        op.drop_index(f"ix_{table_name}_status", table_name=table_name)
        op.drop_table(table_name)

    op.drop_constraint("uq_users_mobile", "users", type_="unique")
    for column in [
        "refresh_token_version",
        "current_session_version",
        "mfa_enabled",
        "password_changed_at",
        "last_login",
        "remember_me",
        "mobile_verified",
        "email_verified",
        "mobile",
    ]:
        op.drop_column("users", column)


def _create_role_profile_table(table_name: str, extra_columns: list[sa.Column] | None = None) -> None:
    columns = [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("specialization", sa.String(length=160), nullable=True),
        sa.Column("qualifications", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("certificates", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("profile_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    ]
    if extra_columns:
        insert_at = 2
        for column in extra_columns:
            columns.insert(insert_at, column)
            insert_at += 1
    op.create_table(table_name, *columns)
    op.create_index(f"ix_{table_name}_status", table_name, ["status"])
