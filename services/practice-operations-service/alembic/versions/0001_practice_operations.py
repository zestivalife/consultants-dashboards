"""External Consultant practice operations foundation."""
from alembic import op

revision="0001_practice_operations"
down_revision=None
branch_labels=None
depends_on=None

TABLES=("practice_consultations","practice_follow_ups","practice_goals","practice_tasks","practice_checkins","practice_adherence_entries","practice_client_notes")


def upgrade():
    for table in TABLES:
        op.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
          id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
          type VARCHAR(80) NOT NULL, title VARCHAR(240) NOT NULL, status VARCHAR(40) NOT NULL,
          due_at TIMESTAMPTZ, payload JSONB NOT NULL DEFAULT '{{}}'::jsonb, version INTEGER NOT NULL DEFAULT 1,
          created_by VARCHAR(120) NOT NULL, idempotency_key VARCHAR(160) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
          CONSTRAINT uq_{table}_tenant_idempotency UNIQUE (tenant_id,idempotency_key)
        )""")
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_client ON {table}(tenant_id,client_id,id DESC)")
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_status_due ON {table}(tenant_id,status,due_at)")
    op.execute("""CREATE TABLE IF NOT EXISTS service_outbox_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, event_type VARCHAR(100) NOT NULL,
      aggregate_type VARCHAR(80) NOT NULL, aggregate_id UUID NOT NULL, payload JSONB NOT NULL DEFAULT '{}'::jsonb,
      status VARCHAR(20) NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
      available_at TIMESTAMPTZ, processed_at TIMESTAMPTZ, last_error TEXT, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_outbox_pending ON service_outbox_events(status,available_at,created_at)")


def downgrade():
    raise RuntimeError("Practice Operations foundation is expand-only")
