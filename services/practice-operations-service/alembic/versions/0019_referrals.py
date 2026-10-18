"""P19 External-only governed referrals and consent."""
from alembic import op

revision="0019_referrals"
down_revision="0018_practice_analytics"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_referrals (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,
      referring_practitioner_id VARCHAR(120) NOT NULL,receiving_practitioner_id VARCHAR(120),
      receiving_tenant_id VARCHAR(80),receiving_profession_code VARCHAR(80) NOT NULL,
      destination_name VARCHAR(240),destination_contact VARCHAR(320),reason TEXT NOT NULL,status VARCHAR(30) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,sent_at TIMESTAMPTZ,accepted_at TIMESTAMPTZ,completed_at TIMESTAMPTZ,
      declined_at TIMESTAMPTZ,cancelled_at TIMESTAMPTZ,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_referral_status CHECK(status IN ('DRAFT','CONSENT_PENDING','READY_TO_SEND','SENT','ACCEPTED','DECLINED','COMPLETED','CANCELLED'))
    )""")
    op.execute("CREATE INDEX ix_external_referrals_source ON external_referrals(tenant_id,client_id,status,created_at DESC)")
    op.execute("CREATE INDEX ix_external_referrals_destination ON external_referrals(receiving_tenant_id,receiving_practitioner_id,status,created_at DESC)")
    op.execute("""CREATE TABLE external_referral_consents (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,referral_id UUID NOT NULL REFERENCES external_referrals(id) ON DELETE RESTRICT,
      client_id VARCHAR(120) NOT NULL,consent_version VARCHAR(40) NOT NULL,status VARCHAR(20) NOT NULL,
      allowed_data_scopes JSONB NOT NULL DEFAULT '[]'::jsonb,consented_at TIMESTAMPTZ,declined_at TIMESTAMPTZ,
      expires_at TIMESTAMPTZ,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_referral_consent_status CHECK(status IN ('PENDING','GRANTED','DECLINED','EXPIRED'))
    )""")
    op.execute("CREATE UNIQUE INDEX uq_external_referral_consent ON external_referral_consents(tenant_id,referral_id)")
    op.execute("""CREATE TABLE external_referral_shared_scopes (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,referral_id UUID NOT NULL REFERENCES external_referrals(id) ON DELETE RESTRICT,
      scope_code VARCHAR(50) NOT NULL,selected_resource_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
      created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,revoked_at TIMESTAMPTZ,
      UNIQUE(tenant_id,referral_id,scope_code)
    )""")
    op.execute("""CREATE TABLE external_referral_events (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,referral_id UUID NOT NULL REFERENCES external_referrals(id) ON DELETE RESTRICT,
      event_type VARCHAR(50) NOT NULL,actor_id VARCHAR(120),actor_type VARCHAR(30) NOT NULL,message TEXT,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_referral_events ON external_referral_events(tenant_id,referral_id,created_at)")
    op.execute("""CREATE TABLE external_referral_audit_events (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,referral_id UUID NOT NULL REFERENCES external_referrals(id) ON DELETE RESTRICT,
      event_type VARCHAR(50) NOT NULL,actor_id VARCHAR(120),actor_type VARCHAR(30) NOT NULL,
      old_value JSONB,new_value JSONB,created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_referral_audit ON external_referral_audit_events(tenant_id,created_at DESC)")

def downgrade():
    raise RuntimeError("Referral management is expand-only")

