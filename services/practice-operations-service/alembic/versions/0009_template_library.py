"""External-only governed template library."""
from alembic import op

revision="0009_template_library"
down_revision="0008_progress_outcomes"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_template_definitions (id UUID PRIMARY KEY, tenant_id VARCHAR(80), profession_code VARCHAR(80) NOT NULL, template_type VARCHAR(30) NOT NULL, scope VARCHAR(20) NOT NULL, owner_id VARCHAR(120), title VARCHAR(240) NOT NULL, description TEXT, active BOOLEAN NOT NULL DEFAULT TRUE, current_version INTEGER NOT NULL DEFAULT 1, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_template_type CHECK (template_type IN ('INTAKE','ASSESSMENT','SESSION_NOTE','PLAN','FOLLOWUP','TASK','MESSAGE','PROGRESS_REPORT')), CONSTRAINT ck_external_template_scope CHECK (scope IN ('SYSTEM','PRACTICE','PRACTITIONER')))""")
    op.execute("CREATE INDEX ix_external_template_library ON external_template_definitions(tenant_id,profession_code,scope,template_type,active)")
    op.execute("""CREATE TABLE external_template_versions (id UUID PRIMARY KEY, definition_id UUID NOT NULL REFERENCES external_template_definitions(id) ON DELETE RESTRICT, tenant_id VARCHAR(80), version INTEGER NOT NULL, title VARCHAR(240) NOT NULL, description TEXT, status VARCHAR(20) NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, CONSTRAINT uq_external_template_version UNIQUE(definition_id,version), CONSTRAINT ck_external_template_version_status CHECK (status IN ('ACTIVE','SUPERSEDED','ARCHIVED')))""")
    op.execute("""CREATE TABLE external_template_sections (id UUID PRIMARY KEY, template_version_id UUID NOT NULL REFERENCES external_template_versions(id) ON DELETE CASCADE, tenant_id VARCHAR(80), section_key VARCHAR(100) NOT NULL, title VARCHAR(240) NOT NULL, description TEXT, sort_order INTEGER NOT NULL, CONSTRAINT uq_external_template_section UNIQUE(template_version_id,section_key))""")
    op.execute("""CREATE TABLE external_template_items (id UUID PRIMARY KEY, section_id UUID NOT NULL REFERENCES external_template_sections(id) ON DELETE CASCADE, tenant_id VARCHAR(80), item_key VARCHAR(100) NOT NULL, label VARCHAR(240) NOT NULL, item_type VARCHAR(40) NOT NULL, config JSONB NOT NULL DEFAULT '{}'::jsonb, sort_order INTEGER NOT NULL, CONSTRAINT uq_external_template_item UNIQUE(section_id,item_key))""")
    op.execute("""CREATE TABLE external_template_audit_events (id UUID PRIMARY KEY, definition_id UUID NOT NULL REFERENCES external_template_definitions(id) ON DELETE RESTRICT, template_version_id UUID REFERENCES external_template_versions(id) ON DELETE RESTRICT, tenant_id VARCHAR(80), event_type VARCHAR(40) NOT NULL, actor_id VARCHAR(120) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL)""")

def downgrade():
    for table in ('external_template_audit_events','external_template_items','external_template_sections','external_template_versions','external_template_definitions'):
        op.execute(f'DROP TABLE IF EXISTS {table}')
