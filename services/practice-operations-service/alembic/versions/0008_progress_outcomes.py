"""External-only profession progress and outcomes."""
from alembic import op

revision="0008_progress_outcomes"
down_revision="0007_structured_notes"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_progress_metric_definitions (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, profession_code VARCHAR(80) NOT NULL, code VARCHAR(100) NOT NULL, label VARCHAR(240) NOT NULL, value_type VARCHAR(24) NOT NULL, unit VARCHAR(60), direction VARCHAR(20), source_type VARCHAR(30) NOT NULL DEFAULT 'MANUAL', active BOOLEAN NOT NULL DEFAULT TRUE, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_progress_metric UNIQUE(tenant_id,code), CONSTRAINT ck_external_progress_source CHECK (source_type IN ('MANUAL','ASSESSMENT','BIOMARKER_REFERENCE')))""")
    op.execute("""CREATE TABLE external_progress_observations (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, metric_definition_id UUID NOT NULL REFERENCES external_progress_metric_definitions(id) ON DELETE RESTRICT, numeric_value NUMERIC, text_value TEXT, source_type VARCHAR(30) NOT NULL, source_id VARCHAR(160), observed_at TIMESTAMPTZ NOT NULL, recorded_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_progress_observations_scope ON external_progress_observations(tenant_id,client_id,metric_definition_id,observed_at DESC)")
    op.execute("""CREATE TABLE external_progress_targets (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, metric_definition_id UUID NOT NULL REFERENCES external_progress_metric_definitions(id) ON DELETE RESTRICT, numeric_target NUMERIC, text_target TEXT, target_date DATE, status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_progress_target_status CHECK (status IN ('ACTIVE','ACHIEVED','CANCELLED')))""")
    op.execute("""CREATE TABLE external_progress_milestones (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, title VARCHAR(240) NOT NULL, description TEXT, status VARCHAR(20) NOT NULL DEFAULT 'PLANNED', target_date DATE, achieved_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_progress_milestone_status CHECK (status IN ('PLANNED','ACHIEVED','CANCELLED')))""")
    op.execute("CREATE INDEX ix_external_progress_milestones_scope ON external_progress_milestones(tenant_id,client_id,status,created_at DESC)")

def downgrade():
    for table in ('external_progress_milestones','external_progress_targets','external_progress_observations','external_progress_metric_definitions'):
        op.execute(f'DROP TABLE IF EXISTS {table}')
