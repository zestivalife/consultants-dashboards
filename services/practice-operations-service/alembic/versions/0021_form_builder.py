"""P21 advanced form builder (External-only, expand-only)."""
from alembic import op

revision = "0021_form_builder"
down_revision = "0020_progress_reports"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""CREATE TABLE external_form_definitions (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, title VARCHAR(240) NOT NULL,
      form_type VARCHAR(60) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', current_version INTEGER NOT NULL DEFAULT 1,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_form_status CHECK(status IN ('DRAFT','PUBLISHED','ARCHIVED')))
    """)
    op.execute("""CREATE TABLE external_form_versions (
      id UUID PRIMARY KEY, definition_id UUID NOT NULL REFERENCES external_form_definitions(id), tenant_id VARCHAR(80) NOT NULL,
      version INTEGER NOT NULL, status VARCHAR(20) NOT NULL, title VARCHAR(240) NOT NULL, settings JSONB NOT NULL DEFAULT '{}'::jsonb,
      published_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      UNIQUE(definition_id,version), CONSTRAINT ck_external_form_version_status CHECK(status IN ('DRAFT','PUBLISHED','SUPERSEDED')))
    """)
    op.execute("""CREATE TABLE external_form_sections (
      id UUID PRIMARY KEY, form_version_id UUID NOT NULL REFERENCES external_form_versions(id), tenant_id VARCHAR(80) NOT NULL,
      section_key VARCHAR(120) NOT NULL, title VARCHAR(240) NOT NULL, description TEXT, sort_order INTEGER NOT NULL,
      UNIQUE(form_version_id,section_key))
    """)
    op.execute("""CREATE TABLE external_form_fields (
      id UUID PRIMARY KEY, section_id UUID NOT NULL REFERENCES external_form_sections(id), tenant_id VARCHAR(80) NOT NULL,
      field_key VARCHAR(120) NOT NULL, label VARCHAR(500) NOT NULL, field_type VARCHAR(40) NOT NULL,
      required BOOLEAN NOT NULL DEFAULT FALSE, config JSONB NOT NULL DEFAULT '{}'::jsonb, condition JSONB,
      sort_order INTEGER NOT NULL, UNIQUE(section_id,field_key))
    """)
    op.execute("""CREATE TABLE external_form_assignments (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      form_definition_id UUID NOT NULL REFERENCES external_form_definitions(id), form_version_id UUID NOT NULL REFERENCES external_form_versions(id),
      linked_type VARCHAR(40), linked_id VARCHAR(120), status VARCHAR(20) NOT NULL DEFAULT 'ASSIGNED', due_at TIMESTAMPTZ,
      assigned_by VARCHAR(120) NOT NULL, assigned_at TIMESTAMPTZ NOT NULL, started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, expires_at TIMESTAMPTZ,
      CONSTRAINT ck_external_form_assignment_status CHECK(status IN ('ASSIGNED','STARTED','COMPLETED','EXPIRED')))
    """)
    op.execute("""CREATE TABLE external_form_responses (
      id UUID PRIMARY KEY, assignment_id UUID NOT NULL REFERENCES external_form_assignments(id), tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL, answers JSONB NOT NULL DEFAULT '{}'::jsonb, status VARCHAR(20) NOT NULL DEFAULT 'STARTED',
      response_version INTEGER NOT NULL DEFAULT 1, submitted_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL,
      UNIQUE(assignment_id), CONSTRAINT ck_external_form_response_status CHECK(status IN ('STARTED','COMPLETED')))
    """)
    op.execute("""CREATE TABLE external_form_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, definition_id UUID, assignment_id UUID,
      event_type VARCHAR(50) NOT NULL, actor_id VARCHAR(120) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL)
    """)
    op.execute("CREATE INDEX ix_external_forms_tenant ON external_form_definitions(tenant_id,status,updated_at)")
    op.execute("CREATE INDEX ix_external_form_assignments_client ON external_form_assignments(tenant_id,client_id,status)")

def downgrade():
    raise RuntimeError("Advanced forms are expand-only")
