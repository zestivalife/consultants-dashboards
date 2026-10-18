"""P29 governed assistive AI Copilot audit foundation."""
from alembic import op
revision="0029_ai_copilot";down_revision="0028_payment_foundation";branch_labels=None;depends_on=None
def upgrade():
    op.execute("""CREATE TABLE external_ai_draft_requests(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120),purpose VARCHAR(40) NOT NULL,instruction TEXT NOT NULL,source_references JSONB NOT NULL DEFAULT '[]'::jsonb,status VARCHAR(24) NOT NULL DEFAULT 'PENDING',requested_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,completed_at TIMESTAMPTZ,CONSTRAINT ck_ai_request_purpose CHECK(purpose IN ('DRAFT','SUMMARISE','PREPARE','SUGGEST')),CONSTRAINT ck_ai_request_status CHECK(status IN ('PENDING','COMPLETED','FAILED','CANCELLED')))""")
    op.execute("""CREATE TABLE external_ai_draft_outputs(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,request_id UUID NOT NULL REFERENCES external_ai_draft_requests(id),classification VARCHAR(24) NOT NULL DEFAULT 'AI_DRAFT',content TEXT NOT NULL,provider VARCHAR(80) NOT NULL,model VARCHAR(120),safety_flags JSONB NOT NULL DEFAULT '[]'::jsonb,accepted BOOLEAN NOT NULL DEFAULT FALSE,accepted_by VARCHAR(120),accepted_at TIMESTAMPTZ,created_at TIMESTAMPTZ NOT NULL,CONSTRAINT ck_ai_output_classification CHECK(classification='AI_DRAFT'))""")
    op.execute("""CREATE TABLE external_ai_audit_events(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,request_id UUID,output_id UUID,event_type VARCHAR(40) NOT NULL,actor_id VARCHAR(120) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_ai_audit_scope ON external_ai_audit_events(tenant_id,created_at DESC)")
def downgrade():raise RuntimeError("AI Copilot foundation is expand-only")
