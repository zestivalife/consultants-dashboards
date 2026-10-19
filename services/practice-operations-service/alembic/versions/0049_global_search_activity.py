"""P49 private per-user recent work metadata."""
from alembic import op
revision='0049_global_search_activity';down_revision='0048_notification_centre';branch_labels=None;depends_on=None
def upgrade():
 op.execute("""CREATE TABLE external_recent_work(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,user_id VARCHAR(120) NOT NULL,resource_type VARCHAR(50) NOT NULL,resource_id VARCHAR(120) NOT NULL,title VARCHAR(240) NOT NULL,route VARCHAR(500) NOT NULL,activity_type VARCHAR(20) NOT NULL CHECK(activity_type IN ('VIEWED','EDITED')),occurred_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,user_id,resource_type,resource_id,activity_type))""")
 op.execute("CREATE INDEX ix_recent_work_user ON external_recent_work(tenant_id,user_id,occurred_at DESC)")
 op.execute("CREATE INDEX ix_search_leads_name ON external_leads(tenant_id,LOWER(first_name),LOWER(last_name))")
 op.execute("CREATE INDEX ix_search_documents_title ON external_documents(tenant_id,LOWER(title))")
 op.execute("CREATE INDEX ix_search_support_subject ON external_support_tickets(tenant_id,LOWER(subject))")
def downgrade():raise RuntimeError('Recent-work audit is expand-only')
