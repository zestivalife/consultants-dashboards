"""External-only nutrition intelligence foundation."""
from alembic import op

revision = "0054_nutrition_foundation"
down_revision = "0053_external_profile"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_nutrition_assessments (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      authorised_consultant_id VARCHAR(120) NOT NULL, status VARCHAR(30) NOT NULL,
      current_version INTEGER NOT NULL CHECK(current_version > 0), review_state VARCHAR(30) NOT NULL,
      consent_state VARCHAR(30) NOT NULL, stale BOOLEAN NOT NULL DEFAULT FALSE, stale_reason TEXT,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_nutrition_assessment_status CHECK(status IN ('DRAFT','IN_REVIEW','APPROVED','CHANGES_REQUESTED')),
      CONSTRAINT ck_external_nutrition_review_state CHECK(review_state IN ('NOT_REVIEWED','IN_REVIEW','REVIEWED','CHANGES_REQUESTED')),
      CONSTRAINT uq_external_nutrition_assessment_version UNIQUE(id,current_version)
    )""")
    op.execute("CREATE INDEX ix_external_nutrition_assessment_client ON external_nutrition_assessments(tenant_id,client_id,updated_at DESC)")
    op.execute("""CREATE TABLE external_nutrition_assessment_versions (
      id UUID PRIMARY KEY, assessment_id UUID NOT NULL REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, version INTEGER NOT NULL,
      source_manifest JSONB NOT NULL, calculation_methodologies JSONB NOT NULL, calculations JSONB NOT NULL,
      input_completeness JSONB NOT NULL, clinical_safety_findings JSONB NOT NULL,
      nutrition_considerations JSONB NOT NULL, provenance JSONB NOT NULL,
      fingerprint_sha256 VARCHAR(64) NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      reviewed_by VARCHAR(120), reviewed_at TIMESTAMPTZ,
      CONSTRAINT uq_external_nutrition_assessment_version_row UNIQUE(assessment_id,version),
      CONSTRAINT uq_external_nutrition_assessment_fingerprint UNIQUE(tenant_id,client_id,fingerprint_sha256),
      CHECK(jsonb_typeof(source_manifest)='array'), CHECK(jsonb_typeof(calculations)='object')
    )""")
    op.execute("CREATE INDEX ix_external_nutrition_version_client ON external_nutrition_assessment_versions(tenant_id,client_id,created_at DESC)")
    op.execute("""CREATE TABLE external_nutrition_assessment_inputs (
      id UUID PRIMARY KEY, assessment_version_id UUID NOT NULL REFERENCES external_nutrition_assessment_versions(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, source_type VARCHAR(60) NOT NULL,
      source_id VARCHAR(160) NOT NULL, source_version VARCHAR(120) NOT NULL, source_status VARCHAR(40) NOT NULL,
      observed_at TIMESTAMPTZ, provenance JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      UNIQUE(assessment_version_id,source_type,source_id,source_version)
    )""")
    op.execute("CREATE INDEX ix_external_nutrition_input_source ON external_nutrition_assessment_inputs(tenant_id,client_id,source_type,source_id)")
    op.execute("""CREATE TABLE external_diet_plan_assessment_links (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      external_plan_id VARCHAR(160) NOT NULL, external_plan_version VARCHAR(120) NOT NULL,
      assessment_id UUID REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT,
      assessment_version INTEGER, source_fingerprint_sha256 VARCHAR(64), calculation_methodologies JSONB NOT NULL DEFAULT '{}'::jsonb,
      plan_state VARCHAR(30) NOT NULL, legacy_lineage_state VARCHAR(40) NOT NULL DEFAULT 'LINKED',
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      UNIQUE(tenant_id,client_id,external_plan_id,external_plan_version),
      CHECK((legacy_lineage_state='LEGACY_UNAVAILABLE' AND assessment_id IS NULL) OR (legacy_lineage_state='LINKED' AND assessment_id IS NOT NULL))
    )""")
    op.execute("CREATE INDEX ix_external_plan_assessment ON external_diet_plan_assessment_links(tenant_id,client_id,assessment_id)")
    op.execute("""CREATE TABLE external_clinical_document_links (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      document_reference VARCHAR(240) NOT NULL, health_record_reference VARCHAR(240), extraction_run_reference VARCHAR(240),
      observation_references JSONB NOT NULL DEFAULT '[]'::jsonb, source_available BOOLEAN NOT NULL,
      source_status VARCHAR(40) NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      UNIQUE(tenant_id,client_id,document_reference), CHECK(jsonb_typeof(observation_references)='array'),
      CHECK((source_available AND source_status='AVAILABLE') OR (NOT source_available AND source_status IN ('HISTORICAL_SOURCE_UNAVAILABLE','QUARANTINED')))
    )""")
    op.execute("""CREATE TABLE external_nutrition_staleness_events (
      id UUID PRIMARY KEY, assessment_id UUID NOT NULL REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, source_type VARCHAR(60) NOT NULL,
      source_id VARCHAR(160) NOT NULL, source_version VARCHAR(120) NOT NULL, reason TEXT NOT NULL,
      resolved_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_nutrition_stale_client ON external_nutrition_staleness_events(tenant_id,client_id,created_at DESC)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS external_nutrition_staleness_events")
    op.execute("DROP TABLE IF EXISTS external_clinical_document_links")
    op.execute("DROP TABLE IF EXISTS external_diet_plan_assessment_links")
    op.execute("DROP TABLE IF EXISTS external_nutrition_assessment_inputs")
    op.execute("DROP TABLE IF EXISTS external_nutrition_assessment_versions")
    op.execute("DROP TABLE IF EXISTS external_nutrition_assessments")

