"""External Consultant to Fiteatsy connection domain (additive only)."""
from alembic import op

revision = "0056_fiteatsy_connections"
down_revision = "0055_nutrition_readiness"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_fiteatsy_connection_invitations (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, consultant_id VARCHAR(120) NOT NULL,
      intended_client_id VARCHAR(120), pin_verifier CHAR(64) NOT NULL UNIQUE, pin_hint CHAR(2) NOT NULL,
      status VARCHAR(20) NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 8,
      expires_at TIMESTAMPTZ NOT NULL, requested_scopes JSONB NOT NULL, redeemed_by_fiteatsy_user_id VARCHAR(120),
      redeemed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_ext_fit_invitation_status CHECK(status IN ('PENDING','REDEEMED','EXPIRED','REVOKED')),
      CONSTRAINT ck_ext_fit_invitation_attempts CHECK(attempt_count >= 0 AND max_attempts BETWEEN 1 AND 20)
    )""")
    op.execute("CREATE INDEX ix_ext_fit_invitation_owner ON external_fiteatsy_connection_invitations(tenant_id,consultant_id,created_at DESC)")
    op.execute("CREATE INDEX ix_ext_fit_invitation_expiry ON external_fiteatsy_connection_invitations(status,expires_at)")
    op.execute("""CREATE TABLE external_fiteatsy_connections (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, consultant_id VARCHAR(120) NOT NULL,
      fiteatsy_user_id VARCHAR(120) NOT NULL, consultant_client_id VARCHAR(120), state VARCHAR(20) NOT NULL,
      consent_version VARCHAR(40) NOT NULL, consented_scopes JSONB NOT NULL, programme_status VARCHAR(30) NOT NULL,
      connected_at TIMESTAMPTZ NOT NULL, disconnected_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_ext_fit_connection UNIQUE(tenant_id,consultant_id,fiteatsy_user_id),
      CONSTRAINT ck_ext_fit_connection_state CHECK(state IN ('ACTIVE','SUSPENDED','DISCONNECTED','REVOKED')),
      CONSTRAINT ck_ext_fit_programme_status CHECK(programme_status IN ('NOT_ENROLLED','INVITED','ACTIVE','PAUSED','COMPLETED','CANCELLED'))
    )""")
    op.execute("CREATE INDEX ix_ext_fit_connection_user ON external_fiteatsy_connections(fiteatsy_user_id,state)")
    op.execute("CREATE INDEX ix_ext_fit_connection_owner ON external_fiteatsy_connections(tenant_id,consultant_id,state)")
    op.execute("""CREATE TABLE external_fiteatsy_consents (
      id UUID PRIMARY KEY, connection_id UUID NOT NULL REFERENCES external_fiteatsy_connections(id) ON DELETE RESTRICT,
      consent_version VARCHAR(40) NOT NULL, scopes JSONB NOT NULL, decision VARCHAR(20) NOT NULL,
      actor_fiteatsy_user_id VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_ext_fit_consent_decision CHECK(decision IN ('GRANTED','WITHDRAWN'))
    )""")
    op.execute("CREATE INDEX ix_ext_fit_consent_history ON external_fiteatsy_consents(connection_id,created_at DESC)")
    op.execute("""CREATE TABLE external_fiteatsy_programmes (
      id UUID PRIMARY KEY, connection_id UUID NOT NULL REFERENCES external_fiteatsy_connections(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, consultant_id VARCHAR(120) NOT NULL, name VARCHAR(240) NOT NULL,
      status VARCHAR(30) NOT NULL, starts_on DATE, ends_on DATE, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_ext_fit_programme_state CHECK(status IN ('DRAFT','INVITED','ACTIVE','PAUSED','COMPLETED','CANCELLED'))
    )""")
    op.execute("CREATE INDEX ix_ext_fit_programmes ON external_fiteatsy_programmes(connection_id,status)")
    op.execute("""CREATE TABLE external_fiteatsy_plan_publications (
      id UUID PRIMARY KEY, connection_id UUID NOT NULL REFERENCES external_fiteatsy_connections(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, consultant_id VARCHAR(120) NOT NULL, plan_id VARCHAR(120) NOT NULL,
      plan_version INTEGER NOT NULL, title VARCHAR(240) NOT NULL, content JSONB NOT NULL, idempotency_key VARCHAR(120) NOT NULL,
      status VARCHAR(20) NOT NULL, published_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_ext_fit_plan_idempotency UNIQUE(connection_id,idempotency_key),
      CONSTRAINT ck_ext_fit_plan_version CHECK(plan_version > 0),
      CONSTRAINT ck_ext_fit_plan_status CHECK(status IN ('PUBLISHED','SUPERSEDED','WITHDRAWN'))
    )""")
    op.execute("CREATE INDEX ix_ext_fit_plans ON external_fiteatsy_plan_publications(connection_id,published_at DESC)")
    op.execute("""CREATE TABLE external_fiteatsy_appointments (
      id UUID PRIMARY KEY, connection_id UUID NOT NULL REFERENCES external_fiteatsy_connections(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, consultant_id VARCHAR(120) NOT NULL, appointment_id VARCHAR(120) NOT NULL,
      title VARCHAR(240) NOT NULL, starts_at TIMESTAMPTZ NOT NULL, ends_at TIMESTAMPTZ NOT NULL,
      idempotency_key VARCHAR(120) NOT NULL, status VARCHAR(20) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_ext_fit_appointment_idempotency UNIQUE(connection_id,idempotency_key),
      CONSTRAINT ck_ext_fit_appointment_window CHECK(ends_at > starts_at),
      CONSTRAINT ck_ext_fit_appointment_status CHECK(status IN ('SCHEDULED','CANCELLED','COMPLETED'))
    )""")
    op.execute("CREATE INDEX ix_ext_fit_appointments ON external_fiteatsy_appointments(connection_id,starts_at)")
    op.execute("""CREATE TABLE external_fiteatsy_connection_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, invitation_id UUID REFERENCES external_fiteatsy_connection_invitations(id) ON DELETE RESTRICT,
      connection_id UUID REFERENCES external_fiteatsy_connections(id) ON DELETE RESTRICT, event_type VARCHAR(50) NOT NULL,
      actor_type VARCHAR(30) NOT NULL, actor_id VARCHAR(120) NOT NULL, event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_ext_fit_event_target CHECK(invitation_id IS NOT NULL OR connection_id IS NOT NULL)
    )""")
    op.execute("CREATE INDEX ix_ext_fit_event_history ON external_fiteatsy_connection_events(tenant_id,created_at DESC)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_connection_events")
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_appointments")
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_plan_publications")
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_programmes")
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_consents")
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_connections")
    op.execute("DROP TABLE IF EXISTS external_fiteatsy_connection_invitations")
