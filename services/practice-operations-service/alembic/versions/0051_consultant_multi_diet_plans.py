"""Consultant-owned multi Diet Plan lifecycle metadata."""
from alembic import op

revision = "0051_multi_diet_plans"
down_revision = "0050_ext_profile_contact_photo"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE external_profession_plans ADD COLUMN IF NOT EXISTS daily_calories_target INTEGER")
    op.execute("ALTER TABLE external_profession_plans ADD COLUMN IF NOT EXISTS daily_protein_target_g NUMERIC(8,2)")
    op.execute("ALTER TABLE external_profession_plans ADD COLUMN IF NOT EXISTS authorised_consultant_id VARCHAR(120)")
    op.execute("ALTER TABLE external_profession_plan_versions ADD COLUMN IF NOT EXISTS nutrition_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE external_profession_plans DROP CONSTRAINT IF EXISTS ck_external_profession_plan_status")
    op.execute("ALTER TABLE external_profession_plans ADD CONSTRAINT ck_external_profession_plan_status CHECK (status IN ('DRAFT','SAVED','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED','APPROVED','PUBLISHED','SUPERSEDED','ARCHIVED'))")
    op.execute("ALTER TABLE external_profession_plan_versions DROP CONSTRAINT IF EXISTS ck_external_profession_plan_version_status")
    op.execute("ALTER TABLE external_profession_plan_versions ADD CONSTRAINT ck_external_profession_plan_version_status CHECK (status IN ('DRAFT','SAVED','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED','APPROVED','PUBLISHED','SUPERSEDED'))")
    op.execute("CREATE INDEX IF NOT EXISTS ix_external_diet_plans_scope ON external_profession_plans(tenant_id,client_id,updated_at DESC) WHERE plan_type='DIET_PLAN'")

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_external_diet_plans_scope")
    op.execute("ALTER TABLE external_profession_plan_versions DROP CONSTRAINT IF EXISTS ck_external_profession_plan_version_status")
    op.execute("ALTER TABLE external_profession_plan_versions ADD CONSTRAINT ck_external_profession_plan_version_status CHECK (status IN ('DRAFT','SAVED','PUBLISHED','SUPERSEDED'))")
    op.execute("ALTER TABLE external_profession_plans DROP CONSTRAINT IF EXISTS ck_external_profession_plan_status")
    op.execute("ALTER TABLE external_profession_plans ADD CONSTRAINT ck_external_profession_plan_status CHECK (status IN ('DRAFT','SAVED','PUBLISHED','SUPERSEDED'))")
    op.execute("ALTER TABLE external_profession_plan_versions DROP COLUMN IF EXISTS nutrition_snapshot")
    op.execute("ALTER TABLE external_profession_plans DROP COLUMN IF EXISTS authorised_consultant_id")
    op.execute("ALTER TABLE external_profession_plans DROP COLUMN IF EXISTS daily_protein_target_g")
    op.execute("ALTER TABLE external_profession_plans DROP COLUMN IF EXISTS daily_calories_target")
