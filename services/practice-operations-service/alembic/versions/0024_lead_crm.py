"""P24 External lead and prospect CRM."""
from alembic import op
revision="0024_lead_crm";down_revision="0023_document_vault";branch_labels=None;depends_on=None
def upgrade():
    op.execute("""CREATE TABLE external_leads(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,first_name VARCHAR(120) NOT NULL,last_name VARCHAR(120),email VARCHAR(320),phone VARCHAR(60),email_key VARCHAR(320),phone_key VARCHAR(60),source VARCHAR(80) NOT NULL,stage VARCHAR(30) NOT NULL DEFAULT 'NEW',assigned_practitioner_id VARCHAR(120),next_follow_up_at TIMESTAMPTZ,notes TEXT,converted_client_id VARCHAR(120),created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,CONSTRAINT ck_external_lead_stage CHECK(stage IN ('NEW','CONTACTED','QUALIFIED','CONSULTATION_BOOKED','CONVERTED','NOT_INTERESTED','LOST')))""")
    op.execute("""CREATE TABLE external_lead_stage_history(id UUID PRIMARY KEY,lead_id UUID NOT NULL REFERENCES external_leads(id),tenant_id VARCHAR(80) NOT NULL,previous_stage VARCHAR(30),resulting_stage VARCHAR(30) NOT NULL,reason VARCHAR(500),actor_id VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("""CREATE TABLE external_lead_follow_ups(id UUID PRIMARY KEY,lead_id UUID NOT NULL REFERENCES external_leads(id),tenant_id VARCHAR(80) NOT NULL,due_at TIMESTAMPTZ NOT NULL,status VARCHAR(20) NOT NULL DEFAULT 'OPEN',note VARCHAR(1000),created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,completed_at TIMESTAMPTZ,CONSTRAINT ck_external_lead_followup_status CHECK(status IN ('OPEN','COMPLETED','CANCELLED')))""")
    op.execute("""CREATE TABLE external_lead_audit_events(id UUID PRIMARY KEY,lead_id UUID NOT NULL REFERENCES external_leads(id),tenant_id VARCHAR(80) NOT NULL,event_type VARCHAR(40) NOT NULL,actor_id VARCHAR(120) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_leads_pipeline ON external_leads(tenant_id,stage,updated_at DESC)")
    op.execute("CREATE INDEX ix_external_leads_duplicates ON external_leads(tenant_id,email_key,phone_key)")
def downgrade():raise RuntimeError("Lead CRM is expand-only")
