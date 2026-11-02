"""Bind governed External QA identities to canonical tenant memberships."""

from alembic import op
import sqlalchemy as sa

revision = "d8e9f0a1b2c3"
down_revision = ("b7c8d9e0f1a2", "c1e2f3a4b5c6")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("external_qa_practice_provisioning", sa.Column("owner_membership_id", sa.String(80), nullable=True))
    op.add_column("external_qa_practice_provisioning", sa.Column("onboarding_id", sa.String(80), nullable=True))
    op.add_column("external_qa_practice_provisioning", sa.Column("account_type", sa.String(40), nullable=False, server_default="PRACTICE_OWNER"))
    op.create_unique_constraint("uq_external_qa_owner_membership", "external_qa_practice_provisioning", ["owner_membership_id"])
    op.create_unique_constraint("uq_external_qa_onboarding", "external_qa_practice_provisioning", ["onboarding_id"])


def downgrade() -> None:
    op.drop_constraint("uq_external_qa_onboarding", "external_qa_practice_provisioning", type_="unique")
    op.drop_constraint("uq_external_qa_owner_membership", "external_qa_practice_provisioning", type_="unique")
    op.drop_column("external_qa_practice_provisioning", "account_type")
    op.drop_column("external_qa_practice_provisioning", "onboarding_id")
    op.drop_column("external_qa_practice_provisioning", "owner_membership_id")
