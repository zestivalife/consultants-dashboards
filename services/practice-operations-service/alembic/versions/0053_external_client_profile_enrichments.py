"""External-only Client360 profile enrichment persistence."""
from alembic import op

revision = "0053_external_profile"
down_revision = "0052_internal_profile"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_client_profile_enrichments (
      tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,
      values JSONB NOT NULL DEFAULT '{}'::jsonb,
      version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
      schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version > 0),
      provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
      audit_history JSONB NOT NULL DEFAULT '[]'::jsonb,
      created_by VARCHAR(120) NOT NULL,
      updated_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY (tenant_id, client_id),
      CHECK (jsonb_typeof(values) = 'object'),
      CHECK (jsonb_typeof(provenance) = 'object'),
      CHECK (jsonb_typeof(audit_history) = 'array')
    )""")
    op.execute("CREATE INDEX ix_external_client_profile_updated ON external_client_profile_enrichments(tenant_id, updated_at DESC)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS external_client_profile_enrichments")
