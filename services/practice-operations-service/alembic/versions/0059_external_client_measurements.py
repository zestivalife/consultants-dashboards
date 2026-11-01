"""Persist versioned external-client measurements used by nutrition assessments."""
from alembic import op

revision = "0059_ext_measurements"
down_revision = "0058_fit_active_plan"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_client_measurements (
      id UUID PRIMARY KEY,
      series_id UUID NOT NULL,
      tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,
      measurement_type VARCHAR(40) NOT NULL,
      value NUMERIC(14,4) NOT NULL,
      unit VARCHAR(12) NOT NULL,
      measured_at TIMESTAMPTZ NOT NULL,
      source VARCHAR(30) NOT NULL,
      recorded_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      version INTEGER NOT NULL,
      supersedes_id UUID REFERENCES external_client_measurements(id) ON DELETE RESTRICT,
      correction_reason VARCHAR(1000),
      CONSTRAINT uq_ext_measurement_series_version UNIQUE(tenant_id,client_id,series_id,version),
      CONSTRAINT ck_ext_measurement_version CHECK(version > 0),
      CONSTRAINT ck_ext_measurement_source CHECK(source IN ('CLIENT_REPORTED','PROFESSIONALLY_RECORDED','DOCUMENT_DERIVED')),
      CONSTRAINT ck_ext_measurement_correction CHECK(
        (version = 1 AND supersedes_id IS NULL AND correction_reason IS NULL)
        OR (version > 1 AND supersedes_id IS NOT NULL AND correction_reason IS NOT NULL)
      )
    )""")
    op.execute("CREATE INDEX ix_ext_measurement_client_timeline ON external_client_measurements(tenant_id,client_id,measured_at DESC,created_at DESC)")
    op.execute("CREATE INDEX ix_ext_measurement_series ON external_client_measurements(tenant_id,client_id,series_id,version DESC)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS external_client_measurements")
