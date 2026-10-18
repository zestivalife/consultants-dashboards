"""P11 external-only lightweight client portal."""
from alembic import op

revision = "0011_client_portal"
down_revision = "0010_session_assistant"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_client_portal_access_grants (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      token_hash VARCHAR(64) NOT NULL UNIQUE, token_version INTEGER NOT NULL DEFAULT 1,
      allowed_actions JSONB NOT NULL DEFAULT '[]'::jsonb, expires_at TIMESTAMPTZ NOT NULL,
      revoked_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, last_used_at TIMESTAMPTZ
    )""")
    op.execute("CREATE INDEX ix_external_client_portal_grant_scope ON external_client_portal_access_grants(tenant_id,client_id,expires_at)")
    op.execute("""CREATE TABLE external_client_portal_documents (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      access_grant_id UUID NOT NULL REFERENCES external_client_portal_access_grants(id) ON DELETE RESTRICT,
      title VARCHAR(240) NOT NULL, document_reference VARCHAR(500) NOT NULL,
      media_type VARCHAR(80) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED',
      submitted_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_client_portal_document_status CHECK (status IN ('SUBMITTED','ACCEPTED','QUARANTINED','REMOVED'))
    )""")
    op.execute("CREATE INDEX ix_external_client_portal_documents_scope ON external_client_portal_documents(tenant_id,client_id,submitted_at DESC)")
    op.execute("""CREATE TABLE external_client_portal_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      access_grant_id UUID REFERENCES external_client_portal_access_grants(id) ON DELETE RESTRICT,
      event_type VARCHAR(60) NOT NULL, actor_type VARCHAR(30) NOT NULL,
      resource_type VARCHAR(60), resource_id VARCHAR(160),
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_client_portal_audit_scope ON external_client_portal_audit_events(tenant_id,client_id,created_at DESC)")


def downgrade():
    for table in (
        "external_client_portal_audit_events",
        "external_client_portal_documents",
        "external_client_portal_access_grants",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
