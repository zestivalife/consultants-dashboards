"""Adopt the canonical versioned external-client measurement table.

Production may already contain this table through the audited External-only
migration ledger. The Alembic branch therefore uses identical additive DDL and
fails closed if an existing table does not match the canonical contract.
"""

from alembic import op
from sqlalchemy import text

revision = "0059_ext_measurements"
down_revision = "0058_fit_active_plan"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS external_client_measurements (
      id UUID PRIMARY KEY,
      series_id UUID NOT NULL,
      tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,
      measurement_type VARCHAR(40) NOT NULL,
      value NUMERIC(10,3) NOT NULL,
      unit VARCHAR(12) NOT NULL,
      measured_at TIMESTAMPTZ NOT NULL,
      source VARCHAR(40) NOT NULL,
      recorded_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      version INTEGER NOT NULL CHECK(version > 0),
      supersedes_id UUID REFERENCES external_client_measurements(id) ON DELETE RESTRICT,
      correction_reason TEXT,
      UNIQUE(series_id,version),
      CHECK(measurement_type IN ('HEIGHT_CM','WEIGHT_KG','WAIST_CM','HIP_CM','NECK_CM','CHEST_CM','MID_UPPER_ARM_CM','THIGH_CM','CALF_CM')),
      CHECK(source IN ('CLIENT_REPORTED','PROFESSIONALLY_RECORDED','DOCUMENT_DERIVED')),
      CHECK((measurement_type='WEIGHT_KG' AND unit='kg') OR (measurement_type<>'WEIGHT_KG' AND unit='cm')),
      CHECK(value > 0),
      CHECK(
        (version = 1 AND supersedes_id IS NULL AND correction_reason IS NULL)
        OR (version > 1 AND supersedes_id IS NOT NULL AND length(correction_reason) >= 3)
      )
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_external_client_measurements_latest ON external_client_measurements(tenant_id,client_id,measurement_type,measured_at DESC,version DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_external_client_measurements_series ON external_client_measurements(tenant_id,client_id,series_id,version DESC)")

    connection = op.get_bind()
    columns = {
        row.column_name: (
            row.data_type,
            row.udt_name,
            row.is_nullable,
            row.numeric_precision,
            row.numeric_scale,
        )
        for row in connection.execute(text("""
          SELECT column_name,data_type,udt_name,is_nullable,numeric_precision,numeric_scale
          FROM information_schema.columns
          WHERE table_schema='public' AND table_name='external_client_measurements'
        """))
    }
    expected = {
        "id": ("uuid", "uuid", "NO", None, None),
        "series_id": ("uuid", "uuid", "NO", None, None),
        "tenant_id": ("character varying", "varchar", "NO", None, None),
        "client_id": ("character varying", "varchar", "NO", None, None),
        "measurement_type": ("character varying", "varchar", "NO", None, None),
        "value": ("numeric", "numeric", "NO", 10, 3),
        "unit": ("character varying", "varchar", "NO", None, None),
        "measured_at": ("timestamp with time zone", "timestamptz", "NO", None, None),
        "source": ("character varying", "varchar", "NO", None, None),
        "recorded_by": ("character varying", "varchar", "NO", None, None),
        "created_at": ("timestamp with time zone", "timestamptz", "NO", None, None),
        "version": ("integer", "int4", "NO", 32, 0),
        "supersedes_id": ("uuid", "uuid", "YES", None, None),
        "correction_reason": ("text", "text", "YES", None, None),
    }
    if columns != expected:
        raise RuntimeError("Existing external_client_measurements schema is not canonical")

    constraint_definitions = "\n".join(
        row.definition
        for row in connection.execute(text("""
          SELECT pg_get_constraintdef(oid) AS definition
          FROM pg_constraint
          WHERE conrelid='external_client_measurements'::regclass
        """))
    )
    required_fragments = (
        "PRIMARY KEY (id)",
        "UNIQUE (series_id, version)",
        "FOREIGN KEY (supersedes_id) REFERENCES external_client_measurements(id) ON DELETE RESTRICT",
        "HEIGHT_CM",
        "WEIGHT_KG",
        "CLIENT_REPORTED",
        "PROFESSIONALLY_RECORDED",
        "DOCUMENT_DERIVED",
    )
    if any(fragment not in constraint_definitions for fragment in required_fragments):
        raise RuntimeError("Existing external_client_measurements constraints are not canonical")


def downgrade():
    raise RuntimeError("External client measurement history is expand-only")
