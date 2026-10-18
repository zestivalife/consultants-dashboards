"""P12 External-only packages, programmes, and renewals."""
from alembic import op

revision = "0012_packages_programmes"
down_revision = "0011_client_portal"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_service_packages (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, name VARCHAR(240) NOT NULL,
      profession_code VARCHAR(80), capability_code VARCHAR(80), description TEXT,
      session_allowance INTEGER NOT NULL, duration_days INTEGER NOT NULL,
      price_minor BIGINT, currency VARCHAR(3), active BOOLEAN NOT NULL DEFAULT TRUE,
      current_version INTEGER NOT NULL DEFAULT 1, created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_package_sessions CHECK (session_allowance > 0),
      CONSTRAINT ck_external_package_duration CHECK (duration_days > 0),
      CONSTRAINT ck_external_package_price CHECK (price_minor IS NULL OR price_minor >= 0),
      CONSTRAINT ck_external_package_currency CHECK ((price_minor IS NULL AND currency IS NULL) OR (price_minor IS NOT NULL AND currency ~ '^[A-Z]{3}$'))
    )""")
    op.execute("CREATE UNIQUE INDEX uq_external_service_package_name ON external_service_packages(tenant_id,lower(name))")
    op.execute("CREATE INDEX ix_external_service_packages_scope ON external_service_packages(tenant_id,active,updated_at DESC)")
    op.execute("""CREATE TABLE external_package_versions (
      id UUID PRIMARY KEY, package_id UUID NOT NULL REFERENCES external_service_packages(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, version INTEGER NOT NULL, snapshot JSONB NOT NULL,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      UNIQUE(package_id,version)
    )""")
    op.execute("CREATE INDEX ix_external_package_versions_scope ON external_package_versions(tenant_id,package_id,version DESC)")
    op.execute("""CREATE TABLE external_client_packages (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      package_id UUID NOT NULL REFERENCES external_service_packages(id) ON DELETE RESTRICT,
      package_version INTEGER NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL,
      status VARCHAR(20) NOT NULL, sessions_total INTEGER NOT NULL, renewal_date DATE,
      notes TEXT, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_client_package_status CHECK (status IN ('DRAFT','ACTIVE','PAUSED','COMPLETED','EXPIRED','CANCELLED')),
      CONSTRAINT ck_external_client_package_dates CHECK (end_date >= start_date),
      CONSTRAINT ck_external_client_package_sessions CHECK (sessions_total > 0)
    )""")
    op.execute("CREATE INDEX ix_external_client_packages_scope ON external_client_packages(tenant_id,client_id,status,end_date)")
    op.execute("""CREATE TABLE external_client_package_sessions (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      client_package_id UUID NOT NULL REFERENCES external_client_packages(id) ON DELETE RESTRICT,
      consultation_id VARCHAR(120), occurred_at TIMESTAMPTZ NOT NULL,
      notes VARCHAR(1000), recorded_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      UNIQUE(tenant_id,client_package_id,consultation_id)
    )""")
    op.execute("CREATE INDEX ix_external_package_sessions_scope ON external_client_package_sessions(tenant_id,client_id,client_package_id,occurred_at DESC)")
    op.execute("""CREATE TABLE external_programme_milestones (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      client_package_id UUID NOT NULL REFERENCES external_client_packages(id) ON DELETE RESTRICT,
      title VARCHAR(240) NOT NULL, due_date DATE, status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
      completed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_programme_milestone_status CHECK (status IN ('PENDING','COMPLETED','CANCELLED'))
    )""")
    op.execute("CREATE INDEX ix_external_programme_milestones_scope ON external_programme_milestones(tenant_id,client_id,client_package_id)")
    op.execute("""CREATE TABLE external_renewal_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      client_package_id UUID NOT NULL REFERENCES external_client_packages(id) ON DELETE RESTRICT,
      signal_type VARCHAR(40) NOT NULL, signal_date DATE NOT NULL, resolved_at TIMESTAMPTZ,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_renewal_signal CHECK (signal_type IN ('PACKAGE_ENDING_SOON','SESSIONS_LOW','NO_FUTURE_SESSION','RENEWAL_DUE','PROGRAMME_EXPIRED')),
      UNIQUE(tenant_id,client_package_id,signal_type,signal_date)
    )""")
    op.execute("CREATE INDEX ix_external_renewal_events_scope ON external_renewal_events(tenant_id,resolved_at,signal_date)")


def downgrade():
    for table in (
        "external_renewal_events", "external_programme_milestones",
        "external_client_package_sessions", "external_client_packages",
        "external_package_versions", "external_service_packages",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
