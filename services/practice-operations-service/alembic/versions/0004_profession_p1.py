"""Profession P1 external-only intake domain."""
from alembic import op

revision = "0004_profession_p1"
down_revision = "0003_phase1_os"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_profession_profiles (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, profession_code VARCHAR(80) NOT NULL,
      display_name VARCHAR(160) NOT NULL, terminology JSONB NOT NULL DEFAULT '{}'::jsonb,
      active BOOLEAN NOT NULL DEFAULT TRUE, version INTEGER NOT NULL DEFAULT 1,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_profession_profile UNIQUE (tenant_id, profession_code)
    )""")
    op.execute("CREATE INDEX ix_external_profession_profiles_tenant ON external_profession_profiles(tenant_id, active, profession_code)")
    op.execute("""CREATE TABLE external_profession_capability_profiles (
      id UUID PRIMARY KEY, profession_profile_id UUID NOT NULL REFERENCES external_profession_profiles(id) ON DELETE CASCADE,
      tenant_id VARCHAR(80) NOT NULL, capability_code VARCHAR(80) NOT NULL, enabled BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_profession_capability UNIQUE (tenant_id, profession_profile_id, capability_code)
    )""")
    op.execute("CREATE INDEX ix_external_profession_capabilities_tenant ON external_profession_capability_profiles(tenant_id, profession_profile_id)")
    op.execute("""CREATE TABLE external_intake_template_versions (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, profession_code VARCHAR(80) NOT NULL,
      version INTEGER NOT NULL, title VARCHAR(200) NOT NULL, status VARCHAR(24) NOT NULL,
      published_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_intake_template_version UNIQUE (tenant_id, profession_code, version),
      CONSTRAINT ck_external_intake_template_status CHECK (status IN ('DRAFT','ACTIVE','RETIRED'))
    )""")
    op.execute("CREATE UNIQUE INDEX uq_external_active_intake_template ON external_intake_template_versions(tenant_id, profession_code) WHERE status='ACTIVE'")
    op.execute("CREATE INDEX ix_external_intake_templates_tenant ON external_intake_template_versions(tenant_id, profession_code, status)")
    op.execute("""CREATE TABLE external_intake_template_sections (
      id UUID PRIMARY KEY, template_version_id UUID NOT NULL REFERENCES external_intake_template_versions(id) ON DELETE CASCADE,
      tenant_id VARCHAR(80) NOT NULL, section_key VARCHAR(80) NOT NULL, title VARCHAR(200) NOT NULL,
      description TEXT, sort_order INTEGER NOT NULL, CONSTRAINT uq_external_intake_section UNIQUE (template_version_id, section_key)
    )""")
    op.execute("CREATE INDEX ix_external_intake_sections_template ON external_intake_template_sections(tenant_id, template_version_id, sort_order)")
    op.execute("""CREATE TABLE external_intake_template_questions (
      id UUID PRIMARY KEY, section_id UUID NOT NULL REFERENCES external_intake_template_sections(id) ON DELETE CASCADE,
      tenant_id VARCHAR(80) NOT NULL, question_key VARCHAR(100) NOT NULL, prompt TEXT NOT NULL,
      question_type VARCHAR(40) NOT NULL, required BOOLEAN NOT NULL DEFAULT FALSE,
      options JSONB NOT NULL DEFAULT '[]'::jsonb, validation JSONB NOT NULL DEFAULT '{}'::jsonb, sort_order INTEGER NOT NULL,
      CONSTRAINT uq_external_intake_question UNIQUE (section_id, question_key)
    )""")
    op.execute("CREATE INDEX ix_external_intake_questions_section ON external_intake_template_questions(tenant_id, section_id, sort_order)")
    op.execute("""CREATE TABLE external_client_intake_instances (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      profession_code VARCHAR(80) NOT NULL, template_version_id UUID NOT NULL REFERENCES external_intake_template_versions(id) ON DELETE RESTRICT,
      status VARCHAR(24) NOT NULL DEFAULT 'NOT_STARTED', completion_percent INTEGER NOT NULL DEFAULT 0,
      token_hash VARCHAR(64) NOT NULL UNIQUE, token_expires_at TIMESTAMPTZ NOT NULL,
      token_version INTEGER NOT NULL DEFAULT 1, review_state VARCHAR(24) NOT NULL DEFAULT 'PENDING',
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, submitted_at TIMESTAMPTZ,
      CONSTRAINT ck_external_intake_instance_status CHECK (status IN ('NOT_STARTED','IN_PROGRESS','COMPLETED','REVOKED','EXPIRED')),
      CONSTRAINT ck_external_intake_completion CHECK (completion_percent BETWEEN 0 AND 100)
    )""")
    op.execute("CREATE INDEX ix_external_intake_instances_client ON external_client_intake_instances(tenant_id, client_id, created_at DESC)")
    op.execute("CREATE INDEX ix_external_intake_instances_active ON external_client_intake_instances(tenant_id, client_id, status) WHERE status IN ('NOT_STARTED','IN_PROGRESS')")
    op.execute("""CREATE TABLE external_client_intake_answers (
      id UUID PRIMARY KEY, intake_instance_id UUID NOT NULL REFERENCES external_client_intake_instances(id) ON DELETE CASCADE,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      question_id UUID NOT NULL REFERENCES external_intake_template_questions(id) ON DELETE RESTRICT,
      answer JSONB NOT NULL, version INTEGER NOT NULL DEFAULT 1, answered_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_intake_answer UNIQUE (intake_instance_id, question_id)
    )""")
    op.execute("CREATE INDEX ix_external_intake_answers_scope ON external_client_intake_answers(tenant_id, client_id, intake_instance_id)")
    op.execute("""CREATE TABLE external_client_intake_custom_questions (
      id UUID PRIMARY KEY, intake_instance_id UUID NOT NULL REFERENCES external_client_intake_instances(id) ON DELETE CASCADE,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, question_key VARCHAR(100) NOT NULL, prompt TEXT NOT NULL,
      question_type VARCHAR(40) NOT NULL, required BOOLEAN NOT NULL DEFAULT FALSE,
      options JSONB NOT NULL DEFAULT '[]'::jsonb, answer JSONB, answer_version INTEGER NOT NULL DEFAULT 0,
      sort_order INTEGER NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_custom_question UNIQUE (intake_instance_id, question_key)
    )""")
    op.execute("CREATE INDEX ix_external_custom_questions_scope ON external_client_intake_custom_questions(tenant_id, client_id, intake_instance_id, sort_order)")
    op.execute("""CREATE TABLE external_client_intake_review_events (
      id UUID PRIMARY KEY, intake_instance_id UUID NOT NULL REFERENCES external_client_intake_instances(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, event_type VARCHAR(40) NOT NULL,
      notes TEXT, actor_id VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_intake_reviews_scope ON external_client_intake_review_events(tenant_id, client_id, intake_instance_id, created_at DESC)")
    op.execute("""CREATE TABLE external_client_intake_audit_events (
      id UUID PRIMARY KEY, intake_instance_id UUID NOT NULL REFERENCES external_client_intake_instances(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, event_type VARCHAR(60) NOT NULL,
      actor_id VARCHAR(120), metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_intake_audit_scope ON external_client_intake_audit_events(tenant_id, client_id, intake_instance_id, created_at DESC)")


def downgrade():
    for table in (
        "external_client_intake_audit_events", "external_client_intake_review_events",
        "external_client_intake_custom_questions", "external_client_intake_answers",
        "external_client_intake_instances", "external_intake_template_questions",
        "external_intake_template_sections", "external_intake_template_versions",
        "external_profession_capability_profiles", "external_profession_profiles",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
