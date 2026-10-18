"""P15 External-only resource library, homework, and adherence."""
from alembic import op

revision = "0015_resources_homework"
down_revision = "0014_billing"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_resource_definitions (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80), scope VARCHAR(20) NOT NULL,
      profession_code VARCHAR(80), title VARCHAR(240) NOT NULL, description TEXT,
      resource_type VARCHAR(30) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE,
      owner_practitioner_id VARCHAR(120), created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_resource_scope CHECK (scope IN ('SYSTEM','PRACTICE','PRACTITIONER')),
      CONSTRAINT ck_external_resource_tenant CHECK ((scope='SYSTEM' AND tenant_id IS NULL) OR (scope<>'SYSTEM' AND tenant_id IS NOT NULL)),
      CONSTRAINT ck_external_resource_type CHECK (resource_type IN ('PDF','DOCUMENT','VIDEO_LINK','ARTICLE_LINK','WORKSHEET','EXERCISE','INSTRUCTION','CHECKLIST','AUDIO_LINK','FORM_LINK'))
    )""")
    op.execute("CREATE INDEX ix_external_resources_tenant ON external_resource_definitions(tenant_id,active,resource_type)")
    op.execute("""CREATE TABLE external_resource_versions (
      id UUID PRIMARY KEY, resource_id UUID NOT NULL REFERENCES external_resource_definitions(id),
      tenant_id VARCHAR(80), version INTEGER NOT NULL, content_reference TEXT NOT NULL,
      media_type VARCHAR(120), duration_minutes INTEGER, instructions TEXT,
      tags JSONB NOT NULL DEFAULT '[]'::jsonb, capability_required VARCHAR(80),
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_resource_version UNIQUE(resource_id,version),
      CONSTRAINT ck_external_resource_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0)
    )""")
    op.execute("""CREATE TABLE external_resource_assignments (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, resource_id UUID NOT NULL REFERENCES external_resource_definitions(id),
      resource_version_id UUID NOT NULL REFERENCES external_resource_versions(id), client_id VARCHAR(120) NOT NULL,
      context_type VARCHAR(20) NOT NULL, context_id VARCHAR(120), assigned_by VARCHAR(120) NOT NULL,
      assigned_at TIMESTAMPTZ NOT NULL, due_at TIMESTAMPTZ, instructions TEXT,
      required BOOLEAN NOT NULL DEFAULT FALSE, status VARCHAR(20) NOT NULL DEFAULT 'ASSIGNED',
      CONSTRAINT ck_external_resource_context CHECK (context_type IN ('CLIENT','SESSION','PLAN','TASK','HOMEWORK','FOLLOWUP')),
      CONSTRAINT ck_external_resource_assignment_status CHECK (status IN ('ASSIGNED','OPENED','COMPLETED','MISSED','CANCELLED'))
    )""")
    op.execute("CREATE INDEX ix_external_resource_assignments_client ON external_resource_assignments(tenant_id,client_id,status,assigned_at)")
    op.execute("""CREATE TABLE external_resource_view_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      assignment_id UUID NOT NULL REFERENCES external_resource_assignments(id), event_type VARCHAR(20) NOT NULL,
      actor_type VARCHAR(20) NOT NULL, actor_id VARCHAR(120), evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_resource_evidence_event CHECK (event_type IN ('OPENED','COMPLETED')),
      CONSTRAINT ck_external_resource_evidence_actor CHECK (actor_type IN ('PRACTITIONER','CLIENT','SYSTEM'))
    )""")
    op.execute("""CREATE TABLE external_homework_assignments (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      profession_code VARCHAR(80), title VARCHAR(240) NOT NULL, description TEXT,
      homework_type VARCHAR(30) NOT NULL, instructions TEXT, assigned_by VARCHAR(120) NOT NULL,
      assigned_at TIMESTAMPTZ NOT NULL, start_date DATE NOT NULL, due_date DATE,
      cadence VARCHAR(30) NOT NULL, every_n_days INTEGER, target_count INTEGER,
      status VARCHAR(20) NOT NULL DEFAULT 'NOT_STARTED', resource_assignment_id UUID REFERENCES external_resource_assignments(id),
      goal_id VARCHAR(120), plan_id UUID, session_id VARCHAR(120), completed_at TIMESTAMPTZ,
      cancelled_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_homework_type CHECK (homework_type IN ('CHECKLIST','REFLECTION','JOURNAL','EXERCISE','HABIT','OBSERVATION_LOG','EDUCATION_TASK','PRACTICE_ACTIVITY','CUSTOM')),
      CONSTRAINT ck_external_homework_cadence CHECK (cadence IN ('ONE_TIME','DAILY','WEEKLY','CUSTOM_INTERVAL')),
      CONSTRAINT ck_external_homework_interval CHECK ((cadence='CUSTOM_INTERVAL' AND every_n_days>0) OR (cadence<>'CUSTOM_INTERVAL' AND every_n_days IS NULL)),
      CONSTRAINT ck_external_homework_status CHECK (status IN ('NOT_STARTED','IN_PROGRESS','COMPLETED','MISSED','CANCELLED'))
    )""")
    op.execute("CREATE INDEX ix_external_homework_client ON external_homework_assignments(tenant_id,client_id,status,due_date)")
    op.execute("""CREATE TABLE external_homework_checkins (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      homework_id UUID NOT NULL REFERENCES external_homework_assignments(id), actor_type VARCHAR(20) NOT NULL,
      actor_id VARCHAR(120), done BOOLEAN, completion_count INTEGER, numeric_adherence NUMERIC(7,2),
      reflection_text TEXT, note TEXT, difficulty_rating INTEGER, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_homework_checkin_actor CHECK (actor_type IN ('PRACTITIONER','CLIENT')),
      CONSTRAINT ck_external_homework_difficulty CHECK (difficulty_rating IS NULL OR difficulty_rating BETWEEN 1 AND 5)
    )""")
    op.execute("""CREATE TABLE external_adherence_observations (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      window_type VARCHAR(30) NOT NULL, window_start DATE NOT NULL, window_end DATE NOT NULL,
      assigned_count INTEGER NOT NULL, completed_count INTEGER NOT NULL, missed_count INTEGER NOT NULL,
      on_time_completed_count INTEGER NOT NULL, completion_rate NUMERIC(7,2), on_time_completion_rate NUMERIC(7,2),
      streak INTEGER, label VARCHAR(30) NOT NULL, last_activity_at TIMESTAMPTZ,
      calculated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_adherence_window UNIQUE(tenant_id,client_id,window_type,window_start,window_end),
      CONSTRAINT ck_external_adherence_window CHECK (window_type IN ('7_DAY','30_DAY','PROGRAMME')),
      CONSTRAINT ck_external_adherence_label CHECK (label IN ('GOOD','MODERATE','NEEDS_ATTENTION','INSUFFICIENT_DATA'))
    )""")
    op.execute("""CREATE TABLE external_resource_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80), client_id VARCHAR(120), resource_id UUID,
      assignment_id UUID, homework_id UUID, event_type VARCHAR(40) NOT NULL,
      actor_id VARCHAR(120), actor_type VARCHAR(20) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_resource_audit_actor CHECK (actor_type IN ('PRACTITIONER','CLIENT','SYSTEM'))
    )""")
    op.execute("CREATE INDEX ix_external_resource_audit ON external_resource_audit_events(tenant_id,client_id,created_at)")


def downgrade():
    op.execute("DROP TABLE external_resource_audit_events")
    op.execute("DROP TABLE external_adherence_observations")
    op.execute("DROP TABLE external_homework_checkins")
    op.execute("DROP TABLE external_homework_assignments")
    op.execute("DROP TABLE external_resource_view_events")
    op.execute("DROP TABLE external_resource_assignments")
    op.execute("DROP TABLE external_resource_versions")
    op.execute("DROP TABLE external_resource_definitions")
