"""P48 per-user notification state and preferences over canonical events."""
from alembic import op
revision='0048_notification_centre';down_revision='0047_platform_support';branch_labels=None;depends_on=None
def upgrade():
 op.execute("""CREATE TABLE external_notification_preferences(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,user_id VARCHAR(120) NOT NULL,in_app BOOLEAN NOT NULL DEFAULT TRUE,email BOOLEAN NOT NULL DEFAULT FALSE,sms BOOLEAN NOT NULL DEFAULT FALSE,whatsapp BOOLEAN NOT NULL DEFAULT FALSE,digest_mode VARCHAR(16) NOT NULL DEFAULT 'IMMEDIATE' CHECK(digest_mode IN ('IMMEDIATE','DAILY','WEEKLY')),category_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,updated_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,user_id))""")
 op.execute("""CREATE TABLE external_notification_user_states(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,user_id VARCHAR(120) NOT NULL,notification_id UUID NOT NULL REFERENCES practice_notifications(id) ON DELETE CASCADE,state VARCHAR(16) NOT NULL CHECK(state IN ('READ','ARCHIVED')),acted_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,user_id,notification_id))""")
 op.execute("CREATE INDEX ix_notification_user_state ON external_notification_user_states(tenant_id,user_id,state,acted_at DESC)")
def downgrade():raise RuntimeError('Notification preference history is expand-only')
