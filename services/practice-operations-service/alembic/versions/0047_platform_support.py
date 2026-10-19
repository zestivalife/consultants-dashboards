"""P47 consultant-platform help desk; not client clinical support."""
from alembic import op
revision='0047_platform_support';down_revision='0046_refunds_credit_notes';branch_labels=None;depends_on=None
def upgrade():
 op.execute("""CREATE TABLE external_support_tickets(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,created_by VARCHAR(120) NOT NULL,ticket_type VARCHAR(30) NOT NULL CHECK(ticket_type IN ('TECHNICAL','ACCOUNT','BILLING','DATA','MARKETPLACE','INTEGRATION','FEATURE_REQUEST','OTHER')),subject VARCHAR(240) NOT NULL,description TEXT NOT NULL,status VARCHAR(30) NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','IN_PROGRESS','WAITING_ON_CUSTOMER','RESOLVED','CLOSED')),priority VARCHAR(10) NOT NULL DEFAULT 'P3' CHECK(priority IN ('P1','P2','P3','P4')),owner_id VARCHAR(120),sla_due_at TIMESTAMPTZ,safe_context JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL)""")
 op.execute("CREATE INDEX ix_support_queue ON external_support_tickets(status,priority,sla_due_at,created_at)")
 op.execute("CREATE INDEX ix_support_tenant ON external_support_tickets(tenant_id,created_at DESC)")
 op.execute("""CREATE TABLE external_support_ticket_events(id UUID PRIMARY KEY,ticket_id UUID NOT NULL REFERENCES external_support_tickets(id) ON DELETE RESTRICT,tenant_id VARCHAR(80) NOT NULL,event_type VARCHAR(40) NOT NULL,previous_status VARCHAR(30),resulting_status VARCHAR(30) NOT NULL,actor_id VARCHAR(120) NOT NULL,message TEXT,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
def downgrade():raise RuntimeError('Support audit history is expand-only')
