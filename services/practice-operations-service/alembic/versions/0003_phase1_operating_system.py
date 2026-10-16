"""External-only profession, communication, notification and timeline foundation."""
from alembic import op

revision = "0003_phase1_os"
down_revision = "0002_practice_completion"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS practice_tenant_configuration (
      tenant_id VARCHAR(80) PRIMARY KEY, profession VARCHAR(60) NOT NULL,
      capabilities JSONB NOT NULL DEFAULT '[]'::jsonb, terminology JSONB NOT NULL DEFAULT '{}'::jsonb,
      profile JSONB NOT NULL DEFAULT '{}'::jsonb, version INTEGER NOT NULL DEFAULT 1,
      updated_by VARCHAR(120) NOT NULL, updated_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS practice_communication_templates (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, code VARCHAR(80) NOT NULL,
      label VARCHAR(120) NOT NULL, body TEXT NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE,
      version INTEGER NOT NULL DEFAULT 1, created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_practice_template_code UNIQUE (tenant_id,code)
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS practice_communication_activity (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      channel VARCHAR(30) NOT NULL, event_type VARCHAR(80) NOT NULL, template_code VARCHAR(80),
      purpose VARCHAR(120) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_practice_communication_client ON practice_communication_activity(tenant_id,client_id,created_at DESC)")
    op.execute("""CREATE TABLE IF NOT EXISTS practice_notifications (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120),
      event_type VARCHAR(80) NOT NULL, title VARCHAR(240) NOT NULL,
      payload JSONB NOT NULL DEFAULT '{}'::jsonb, read_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_practice_notifications ON practice_notifications(tenant_id,read_at,created_at DESC)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_practice_onboarding_complete_notification ON practice_notifications(tenant_id,event_type,client_id) WHERE event_type='ONBOARDING_COMPLETED'")
    op.execute("""CREATE TABLE IF NOT EXISTS practice_timeline_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      event_type VARCHAR(80) NOT NULL, source_type VARCHAR(80) NOT NULL,
      source_id VARCHAR(160), summary VARCHAR(300) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb, occurred_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_practice_timeline_source UNIQUE (tenant_id,event_type,source_type,source_id)
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_practice_timeline_client ON practice_timeline_events(tenant_id,client_id,occurred_at DESC,id DESC)")


def downgrade():
    raise RuntimeError("Practice Operating System Phase 1 is expand-only")
