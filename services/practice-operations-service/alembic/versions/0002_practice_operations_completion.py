"""Complete external practice operations projections without duplicating media storage."""
from alembic import op

revision = "0002_practice_operations_completion"
down_revision = "0001_practice_operations"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS practice_goal_progress_entries (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, goal_id UUID NOT NULL,
      client_id VARCHAR(120) NOT NULL, recorded_at TIMESTAMPTZ NOT NULL,
      value DOUBLE PRECISION NOT NULL, unit VARCHAR(32) NOT NULL, note TEXT,
      created_by VARCHAR(120) NOT NULL, idempotency_key VARCHAR(160) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_goal_progress_tenant_idempotency UNIQUE (tenant_id,idempotency_key)
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_goal_progress_history ON practice_goal_progress_entries(tenant_id,goal_id,recorded_at DESC,id DESC)")
    op.execute("""CREATE TABLE IF NOT EXISTS practice_media_references (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      captured_at TIMESTAMPTZ NOT NULL, media_type VARCHAR(40) NOT NULL,
      document_reference VARCHAR(500) NOT NULL, meal VARCHAR(120), note TEXT,
      created_by VARCHAR(120) NOT NULL, idempotency_key VARCHAR(160) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_media_reference_tenant_idempotency UNIQUE (tenant_id,idempotency_key)
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_media_reference_client ON practice_media_references(tenant_id,client_id,captured_at DESC)")
    op.execute("""CREATE TABLE IF NOT EXISTS service_outbox_deliveries (
      consumer_name VARCHAR(120) NOT NULL, event_id UUID NOT NULL,
      tenant_id VARCHAR(80) NOT NULL, delivered_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (consumer_name,event_id)
    )""")


def downgrade():
    raise RuntimeError("Practice Operations completion is expand-only")
