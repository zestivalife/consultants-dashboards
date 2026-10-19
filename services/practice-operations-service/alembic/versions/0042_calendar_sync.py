"""P42 external-only calendar sync foundation."""
from alembic import op

revision="0042_calendar_sync";down_revision="0041_secure_messaging";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_calendar_connections(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,user_id VARCHAR(120) NOT NULL,provider VARCHAR(20) NOT NULL CHECK(provider IN ('GOOGLE','MICROSOFT')),status VARCHAR(30) NOT NULL DEFAULT 'NOT_CONFIGURED' CHECK(status IN ('NOT_CONFIGURED','CONNECTED','REAUTH_REQUIRED','DISCONNECTED')),credential_secret_reference VARCHAR(240),sync_cursor_encrypted TEXT,last_synced_at TIMESTAMPTZ,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,user_id,provider),CHECK(status='NOT_CONFIGURED' OR credential_secret_reference IS NOT NULL))""")
    op.execute("CREATE INDEX ix_calendar_connections_scope ON external_calendar_connections(tenant_id,user_id,status)")
    op.execute("""CREATE TABLE external_calendar_busy_blocks(id UUID PRIMARY KEY,connection_id UUID NOT NULL REFERENCES external_calendar_connections(id) ON DELETE RESTRICT,tenant_id VARCHAR(80) NOT NULL,provider_event_hash VARCHAR(128) NOT NULL,starts_at TIMESTAMPTZ NOT NULL,ends_at TIMESTAMPTZ NOT NULL,visibility VARCHAR(10) NOT NULL DEFAULT 'BUSY' CHECK(visibility='BUSY'),active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,CHECK(ends_at>starts_at),UNIQUE(connection_id,provider_event_hash))""")
    op.execute("CREATE INDEX ix_calendar_busy_scope ON external_calendar_busy_blocks(tenant_id,starts_at,ends_at) WHERE active=TRUE")
    op.execute("""CREATE TABLE external_calendar_sync_events(id UUID PRIMARY KEY,connection_id UUID NOT NULL REFERENCES external_calendar_connections(id) ON DELETE RESTRICT,tenant_id VARCHAR(80) NOT NULL,appointment_id UUID REFERENCES external_scheduled_appointments(id) ON DELETE RESTRICT,event_type VARCHAR(50) NOT NULL CHECK(event_type IN ('CONNECTION_CONFIGURED','SYNC_COMPLETED','SYNC_FAILED','EXTERNAL_CHANGE_DETECTED','EXTERNAL_CHANGE_CONFIRMED','EXTERNAL_CHANGE_DISMISSED')),external_change_type VARCHAR(20) CHECK(external_change_type IN ('RESCHEDULE','CANCEL')),actor_id VARCHAR(120),metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")

def downgrade():raise RuntimeError("Calendar sync is expand-only")
