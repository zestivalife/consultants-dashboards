"""P20 External-only immutable progress reports."""
from alembic import op

revision="0020_progress_reports"
down_revision="0019_referrals"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_progress_reports (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,
      profession_code VARCHAR(80) NOT NULL,report_type VARCHAR(60) NOT NULL,title VARCHAR(240) NOT NULL,
      period_start DATE NOT NULL,period_end DATE NOT NULL,included_sections JSONB NOT NULL,
      consultant_summary TEXT,status VARCHAR(20) NOT NULL,current_version INTEGER NOT NULL DEFAULT 0,
      created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      shared_at TIMESTAMPTZ,shared_by VARCHAR(120),revoked_at TIMESTAMPTZ,
      CONSTRAINT ck_external_progress_report_period CHECK(period_end>=period_start),
      CONSTRAINT ck_external_progress_report_status CHECK(status IN ('DRAFT','GENERATED','SHARED','REVOKED'))
    )""")
    op.execute("CREATE INDEX ix_external_progress_reports_scope ON external_progress_reports(tenant_id,client_id,status,created_at DESC)")
    op.execute("""CREATE TABLE external_progress_report_versions (
      id UUID PRIMARY KEY,report_id UUID NOT NULL REFERENCES external_progress_reports(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,version INTEGER NOT NULL,
      source_snapshot JSONB NOT NULL,checksum VARCHAR(64) NOT NULL,generated_by VARCHAR(120) NOT NULL,
      generated_at TIMESTAMPTZ NOT NULL,UNIQUE(report_id,version)
    )""")
    op.execute("CREATE INDEX ix_external_progress_report_versions ON external_progress_report_versions(tenant_id,client_id,report_id,version DESC)")
    op.execute("""CREATE TABLE external_progress_report_artifacts (
      id UUID PRIMARY KEY,report_version_id UUID NOT NULL REFERENCES external_progress_report_versions(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,format VARCHAR(10) NOT NULL,media_type VARCHAR(120) NOT NULL,
      content_bytes BYTEA NOT NULL,checksum VARCHAR(64) NOT NULL,created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_progress_artifact_format CHECK(format IN ('PDF','DOCX')),
      UNIQUE(report_version_id,format)
    )""")
    op.execute("""CREATE TABLE external_progress_report_audit_events (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,
      report_id UUID NOT NULL REFERENCES external_progress_reports(id) ON DELETE RESTRICT,
      report_version_id UUID REFERENCES external_progress_report_versions(id) ON DELETE RESTRICT,
      event_type VARCHAR(50) NOT NULL,actor_id VARCHAR(120) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_progress_report_audit ON external_progress_report_audit_events(tenant_id,report_id,created_at)")

def downgrade():
    raise RuntimeError("Progress reports are expand-only")
