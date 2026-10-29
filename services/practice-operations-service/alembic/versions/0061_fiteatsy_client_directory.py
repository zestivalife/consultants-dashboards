"""Canonical Fiteatsy client-directory projection and delivery ledger."""
from alembic import op

revision = "0061_fiteatsy_directory"
down_revision = "0060_fit_pin_rate_limit"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE fiteatsy_client_directory (
      id UUID PRIMARY KEY,
      fiteatsy_user_id UUID NOT NULL UNIQUE,
      fiteatsy_client_id VARCHAR(120),
      display_name VARCHAR(240) NOT NULL,
      mobile_number_normalized VARCHAR(32),
      email_normalized VARCHAR(320),
      account_status VARCHAR(30) NOT NULL,
      mobile_verified BOOLEAN NOT NULL,
      registration_status VARCHAR(30) NOT NULL,
      registered_at TIMESTAMPTZ NOT NULL,
      source_updated_at TIMESTAMPTZ NOT NULL,
      source_version INTEGER NOT NULL,
      last_synced_at TIMESTAMPTZ NOT NULL,
      sync_status VARCHAR(30) NOT NULL,
      deleted_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_fit_directory_version CHECK(source_version > 0),
      CONSTRAINT ck_fit_directory_sync CHECK(sync_status IN ('CURRENT','STALE','ERROR')),
      CONSTRAINT ck_fit_directory_registration CHECK(registration_status IN ('PENDING','COMPLETED'))
    )""")
    op.execute("CREATE INDEX ix_fit_directory_mobile ON fiteatsy_client_directory(mobile_number_normalized) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_fit_directory_registered ON fiteatsy_client_directory(registered_at DESC, fiteatsy_user_id DESC)")
    op.execute("CREATE INDEX ix_fit_directory_status ON fiteatsy_client_directory(account_status,registration_status) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_fit_directory_sync ON fiteatsy_client_directory(last_synced_at,sync_status)")
    op.execute("""CREATE TABLE fiteatsy_client_directory_events (
      event_id UUID PRIMARY KEY,
      event_type VARCHAR(60) NOT NULL,
      fiteatsy_user_id UUID NOT NULL,
      source_version INTEGER NOT NULL,
      schema_version INTEGER NOT NULL,
      payload_sha256 VARCHAR(64) NOT NULL,
      occurred_at TIMESTAMPTZ NOT NULL,
      processed_at TIMESTAMPTZ NOT NULL,
      disposition VARCHAR(30) NOT NULL,
      CONSTRAINT ck_fit_directory_event_disposition CHECK(disposition IN ('APPLIED','STALE','DUPLICATE'))
    )""")
    op.execute("CREATE INDEX ix_fit_directory_event_user ON fiteatsy_client_directory_events(fiteatsy_user_id,source_version DESC)")
    op.execute("""CREATE TABLE fiteatsy_client_directory_reconciliation_runs (
      id UUID PRIMARY KEY,
      started_at TIMESTAMPTZ NOT NULL,
      completed_at TIMESTAMPTZ,
      source_count INTEGER,
      destination_count INTEGER,
      missing_count INTEGER,
      stale_count INTEGER,
      duplicate_count INTEGER,
      status VARCHAR(30) NOT NULL,
      checkpoint_user_id UUID,
      error_code VARCHAR(80),
      CONSTRAINT ck_fit_directory_reconcile_status CHECK(status IN ('RUNNING','COMPLETED','FAILED'))
    )""")


def downgrade():
    raise RuntimeError("Fiteatsy client-directory persistence is expand-only")
