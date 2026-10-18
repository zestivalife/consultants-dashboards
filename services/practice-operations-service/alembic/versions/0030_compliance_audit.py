"""P30 External compliance, export, and audit centre."""
from alembic import op
revision="0030_compliance_audit";down_revision="0029_ai_copilot";branch_labels=None;depends_on=None
def upgrade():
    op.execute("""CREATE TABLE external_data_export_requests(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,sections JSONB NOT NULL DEFAULT '[]'::jsonb,status VARCHAR(24) NOT NULL DEFAULT 'COMPLETED',private_notes_included BOOLEAN NOT NULL DEFAULT FALSE,requested_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,completed_at TIMESTAMPTZ,content_checksum VARCHAR(64),CONSTRAINT ck_export_status CHECK(status IN ('PENDING','COMPLETED','FAILED','EXPIRED')),CONSTRAINT ck_export_private_notes CHECK(private_notes_included=FALSE))""")
    op.execute("""CREATE TABLE external_compliance_audit_events(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120),event_type VARCHAR(50) NOT NULL,actor_id VARCHAR(120) NOT NULL,resource_type VARCHAR(50),resource_id VARCHAR(120),metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_compliance_audit ON external_compliance_audit_events(tenant_id,client_id,created_at DESC)")
def downgrade():raise RuntimeError("Compliance audit is expand-only")
