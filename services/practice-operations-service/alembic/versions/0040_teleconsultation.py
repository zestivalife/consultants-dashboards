"""P40 External-only teleconsultation session authority."""
from alembic import op
revision="0040_teleconsultation";down_revision="0039_client_feedback";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_teleconsult_sessions(
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,appointment_id UUID NOT NULL REFERENCES external_scheduled_appointments(id) ON DELETE RESTRICT,
      client_id VARCHAR(120) NOT NULL,consultant_id VARCHAR(120) NOT NULL,
      provider_mode VARCHAR(40) NOT NULL CHECK(provider_mode IN ('BUILT_IN_PROVIDER','EXTERNAL_MEETING_LINK','PROVIDER_NOT_CONFIGURED')),
      external_meeting_url TEXT,status VARCHAR(30) NOT NULL DEFAULT 'UPCOMING' CHECK(status IN ('UPCOMING','WAITING_FOR_CONSULTANT','SESSION_ACTIVE','SESSION_COMPLETED','CANCELLED')),
      join_window_before_minutes INTEGER NOT NULL DEFAULT 15 CHECK(join_window_before_minutes BETWEEN 0 AND 240),
      join_window_after_minutes INTEGER NOT NULL DEFAULT 30 CHECK(join_window_after_minutes BETWEEN 0 AND 480),
      started_at TIMESTAMPTZ,completed_at TIMESTAMPTZ,created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      UNIQUE(tenant_id,appointment_id),CHECK(provider_mode<>'EXTERNAL_MEETING_LINK' OR external_meeting_url IS NOT NULL))""")
    op.execute("CREATE INDEX ix_teleconsult_scope ON external_teleconsult_sessions(tenant_id,client_id,status,updated_at DESC)")
    op.execute("""CREATE TABLE external_teleconsult_events(
      id UUID PRIMARY KEY,session_id UUID NOT NULL REFERENCES external_teleconsult_sessions(id) ON DELETE RESTRICT,tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,event_type VARCHAR(50) NOT NULL CHECK(event_type IN ('SESSION_CONFIGURED','CLIENT_JOINED_WAITING_ROOM','SESSION_STARTED','SESSION_COMPLETED','SESSION_CANCELLED')),
      actor_id VARCHAR(120),actor_type VARCHAR(30) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_teleconsult_events_scope ON external_teleconsult_events(tenant_id,session_id,created_at)")

def downgrade():raise RuntimeError("Teleconsultation authority is expand-only")
