"""P18 External-only analytics snapshots and audit."""
from alembic import op

revision = "0018_practice_analytics"
down_revision = "0017_team_practice_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_analytics_snapshots (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, snapshot_type VARCHAR(50) NOT NULL,
      period_start TIMESTAMPTZ NOT NULL, period_end TIMESTAMPTZ NOT NULL,
      filters JSONB NOT NULL DEFAULT '{}'::jsonb, aggregate_data JSONB NOT NULL,
      cohort_size INTEGER, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_analytics_period CHECK (period_end > period_start),
      CONSTRAINT ck_external_analytics_cohort CHECK (cohort_size IS NULL OR cohort_size >= 0)
    )""")
    op.execute("CREATE INDEX ix_external_analytics_snapshot_scope ON external_analytics_snapshots(tenant_id,snapshot_type,period_end DESC)")
    op.execute("""CREATE TABLE external_analytics_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, event_type VARCHAR(50) NOT NULL,
      actor_id VARCHAR(120) NOT NULL, snapshot_id UUID REFERENCES external_analytics_snapshots(id) ON DELETE RESTRICT,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_analytics_audit_scope ON external_analytics_audit_events(tenant_id,created_at DESC)")


def downgrade():
    raise RuntimeError("Practice analytics is expand-only")

