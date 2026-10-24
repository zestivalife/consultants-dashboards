"""External-only Nutrition Assessment workflow and readiness."""
from alembic import op

revision = "0055_nutrition_readiness"
down_revision = "0054_nutrition_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE external_nutrition_assessments DROP CONSTRAINT ck_external_nutrition_assessment_status")
    op.execute("ALTER TABLE external_nutrition_assessments ADD CONSTRAINT ck_external_nutrition_assessment_status CHECK(status IN ('DRAFT','SUBMITTED','IN_REVIEW','REVIEWED','CHANGES_REQUESTED'))")
    op.execute("ALTER TABLE external_nutrition_assessments ADD COLUMN readiness_status VARCHAR(30) NOT NULL DEFAULT 'NOT_STARTED'")
    op.execute("ALTER TABLE external_nutrition_assessments ADD CONSTRAINT ck_external_nutrition_readiness CHECK(readiness_status IN ('NOT_STARTED','INCOMPLETE','NEEDS_REVIEW','READY','BLOCKED'))")
    op.execute("ALTER TABLE external_nutrition_assessment_versions ADD COLUMN assessment_data JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE external_nutrition_assessment_versions ADD COLUMN readiness JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute("CREATE TABLE external_nutrition_assessment_events (id UUID PRIMARY KEY, assessment_id UUID NOT NULL REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, assessment_version INTEGER NOT NULL, event_type VARCHAR(40) NOT NULL, from_status VARCHAR(30), to_status VARCHAR(30) NOT NULL, notes TEXT, actor_id VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL)")
    op.execute("CREATE INDEX ix_external_nutrition_event_history ON external_nutrition_assessment_events(tenant_id,client_id,created_at DESC)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS external_nutrition_assessment_events")
    op.execute("ALTER TABLE external_nutrition_assessment_versions DROP COLUMN IF EXISTS readiness")
    op.execute("ALTER TABLE external_nutrition_assessment_versions DROP COLUMN IF EXISTS assessment_data")
    op.execute("ALTER TABLE external_nutrition_assessments DROP CONSTRAINT IF EXISTS ck_external_nutrition_readiness")
    op.execute("ALTER TABLE external_nutrition_assessments DROP COLUMN IF EXISTS readiness_status")
    op.execute("ALTER TABLE external_nutrition_assessments DROP CONSTRAINT ck_external_nutrition_assessment_status")
    op.execute("ALTER TABLE external_nutrition_assessments ADD CONSTRAINT ck_external_nutrition_assessment_status CHECK(status IN ('DRAFT','IN_REVIEW','APPROVED','CHANGES_REQUESTED'))")
