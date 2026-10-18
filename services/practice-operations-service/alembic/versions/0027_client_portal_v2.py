"""P27 additive Client Portal 2.0 preferences and notification state."""
from alembic import op
revision="0027_client_portal_v2";down_revision="0026_multi_location";branch_labels=None;depends_on=None
def upgrade():
    op.execute("""CREATE TABLE external_client_portal_preferences(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,notification_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,accessibility_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,updated_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,client_id))""")
    op.execute("""CREATE TABLE external_client_portal_notification_reads(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,preparation_id UUID NOT NULL REFERENCES external_communication_preparations(id),read_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,client_id,preparation_id))""")
def downgrade():raise RuntimeError("Client Portal 2.0 is expand-only")
