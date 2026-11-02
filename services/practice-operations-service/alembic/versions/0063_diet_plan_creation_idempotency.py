"""Make consultant Diet Plan draft creation idempotent."""

from alembic import op


revision = "0063_diet_plan_creation_idempotency"
down_revision = "0062_merge_release_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE external_profession_plans ADD COLUMN idempotency_key VARCHAR(160)")
    op.execute("""CREATE UNIQUE INDEX uq_external_diet_plan_creation_idempotency
        ON external_profession_plans(tenant_id,authorised_consultant_id,idempotency_key)
        WHERE plan_type='DIET_PLAN' AND idempotency_key IS NOT NULL""")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_external_diet_plan_creation_idempotency")
    op.execute("ALTER TABLE external_profession_plans DROP COLUMN IF EXISTS idempotency_key")
