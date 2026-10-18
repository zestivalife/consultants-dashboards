"""Add External-only practice roles, invitations, assignments, and audit."""
from alembic import op

revision = "0017_team_practice_rbac"
down_revision = "0016_workflow_automation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_practice_role_profiles (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, user_id VARCHAR(120) NOT NULL,
      role VARCHAR(40) NOT NULL, status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', display_name VARCHAR(240),
      profession_code VARCHAR(80), specialisation VARCHAR(160), location_code VARCHAR(120),
      permission_grants JSONB NOT NULL DEFAULT '[]'::jsonb, permission_restrictions JSONB NOT NULL DEFAULT '[]'::jsonb,
      practice_wide_client_access BOOLEAN NOT NULL DEFAULT FALSE, active_from TIMESTAMPTZ NOT NULL,
      active_until TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_practice_role UNIQUE (tenant_id,user_id),
      CONSTRAINT ck_external_practice_role CHECK (role IN ('PRACTICE_OWNER','PRACTICE_ADMIN','PRACTITIONER','ASSISTANT','RECEPTIONIST')),
      CONSTRAINT ck_external_practice_status CHECK (status IN ('INVITED','ACTIVE','SUSPENDED','DEACTIVATED')),
      CONSTRAINT ck_external_practitioner_profession CHECK (role <> 'PRACTITIONER' OR profession_code IS NOT NULL)
    )""")
    op.execute("CREATE INDEX ix_external_practice_roles_tenant ON external_practice_role_profiles(tenant_id,status,role)")
    op.execute("""CREATE TABLE external_team_invitations (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, email VARCHAR(320) NOT NULL, display_name VARCHAR(240) NOT NULL,
      role VARCHAR(40) NOT NULL, profession_code VARCHAR(80), specialisation VARCHAR(160), location_code VARCHAR(120),
      permission_grants JSONB NOT NULL DEFAULT '[]'::jsonb, permission_restrictions JSONB NOT NULL DEFAULT '[]'::jsonb,
      token_hash VARCHAR(128) NOT NULL UNIQUE, status VARCHAR(30) NOT NULL, invited_by VARCHAR(120) NOT NULL,
      expires_at TIMESTAMPTZ NOT NULL, accepted_by VARCHAR(120), accepted_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_invite_role CHECK (role IN ('PRACTICE_ADMIN','PRACTITIONER','ASSISTANT','RECEPTIONIST'))
    )""")
    op.execute("CREATE INDEX ix_external_team_invites_tenant ON external_team_invitations(tenant_id,status,created_at DESC)")
    op.execute("""CREATE TABLE external_client_team_assignments (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, user_id VARCHAR(120) NOT NULL,
      assignment_role VARCHAR(40) NOT NULL, assigned_by VARCHAR(120) NOT NULL, assigned_at TIMESTAMPTZ NOT NULL,
      ended_at TIMESTAMPTZ, reason VARCHAR(500),
      CONSTRAINT ck_external_assignment_role CHECK (assignment_role IN ('PRIMARY_PRACTITIONER','SECONDARY_PRACTITIONER','CARE_TEAM_MEMBER'))
    )""")
    op.execute("CREATE UNIQUE INDEX uq_external_active_client_assignment ON external_client_team_assignments(tenant_id,client_id,user_id,assignment_role) WHERE ended_at IS NULL")
    op.execute("CREATE UNIQUE INDEX uq_external_primary_practitioner ON external_client_team_assignments(tenant_id,client_id) WHERE ended_at IS NULL AND assignment_role='PRIMARY_PRACTITIONER'")
    op.execute("""CREATE TABLE external_team_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, event_type VARCHAR(60) NOT NULL,
      actor_id VARCHAR(120) NOT NULL, target_user_id VARCHAR(120), client_id VARCHAR(120),
      old_value JSONB, new_value JSONB, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_team_audit_tenant ON external_team_audit_events(tenant_id,created_at DESC)")
    op.execute("""CREATE TABLE external_team_locations (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, code VARCHAR(120) NOT NULL, name VARCHAR(240) NOT NULL,
      active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_team_location UNIQUE (tenant_id,code)
    )""")


def downgrade():
    raise RuntimeError("Team practice RBAC is expand-only")
