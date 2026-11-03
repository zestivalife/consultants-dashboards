"""Canonical tenant-scoped clients created by an external practice."""
from alembic import op

revision = "0064_external_practice_clients"
down_revision = "0063_diet_plan_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_practice_clients (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      first_name VARCHAR(120) NOT NULL, last_name VARCHAR(120) NOT NULL DEFAULT '',
      email VARCHAR(320), email_key VARCHAR(320), mobile VARCHAR(32), mobile_key VARCHAR(32),
      status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE', created_by VARCHAR(120) NOT NULL,
      idempotency_key VARCHAR(160) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      UNIQUE (tenant_id, client_id), UNIQUE (tenant_id, idempotency_key),
      CHECK (email_key IS NOT NULL OR mobile_key IS NOT NULL), CHECK (status IN ('ACTIVE','ARCHIVED'))
    )""")
    op.execute("CREATE UNIQUE INDEX uq_external_practice_client_email ON external_practice_clients(tenant_id,email_key) WHERE email_key IS NOT NULL AND status='ACTIVE'")
    op.execute("CREATE UNIQUE INDEX uq_external_practice_client_mobile ON external_practice_clients(tenant_id,mobile_key) WHERE mobile_key IS NOT NULL AND status='ACTIVE'")


def downgrade():
    op.execute("DROP TABLE IF EXISTS external_practice_clients")
