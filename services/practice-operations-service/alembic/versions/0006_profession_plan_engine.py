"""External-only profession plan engine."""
from alembic import op

revision="0006_profession_plan_engine"
down_revision="0005_assessment_engine"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_profession_plans (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, profession_code VARCHAR(80) NOT NULL, plan_type VARCHAR(60) NOT NULL, title VARCHAR(240) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', current_version INTEGER NOT NULL DEFAULT 1, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_profession_plan_status CHECK (status IN ('DRAFT','SAVED','PUBLISHED','SUPERSEDED')))""")
    op.execute("CREATE INDEX ix_external_profession_plans_scope ON external_profession_plans(tenant_id,client_id,plan_type,status,updated_at DESC)")
    op.execute("""CREATE TABLE external_profession_plan_versions (id UUID PRIMARY KEY, plan_id UUID NOT NULL REFERENCES external_profession_plans(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, version INTEGER NOT NULL, status VARCHAR(20) NOT NULL, title VARCHAR(240) NOT NULL, published_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_profession_plan_version_status CHECK (status IN ('DRAFT','SAVED','PUBLISHED','SUPERSEDED')), CONSTRAINT uq_external_profession_plan_version UNIQUE(plan_id,version))""")
    op.execute("""CREATE TABLE external_profession_plan_sections (id UUID PRIMARY KEY, plan_version_id UUID NOT NULL REFERENCES external_profession_plan_versions(id) ON DELETE CASCADE, tenant_id VARCHAR(80) NOT NULL, section_key VARCHAR(100) NOT NULL, title VARCHAR(240) NOT NULL, content JSONB NOT NULL DEFAULT '{}'::jsonb, sort_order INTEGER NOT NULL, CONSTRAINT uq_external_profession_plan_section UNIQUE(plan_version_id,section_key))""")
    op.execute("""CREATE TABLE external_profession_plan_items (id UUID PRIMARY KEY, plan_section_id UUID NOT NULL REFERENCES external_profession_plan_sections(id) ON DELETE CASCADE, tenant_id VARCHAR(80) NOT NULL, item_key VARCHAR(100) NOT NULL, label VARCHAR(240) NOT NULL, content JSONB NOT NULL DEFAULT '{}'::jsonb, sort_order INTEGER NOT NULL, CONSTRAINT uq_external_profession_plan_item UNIQUE(plan_section_id,item_key))""")
    op.execute("""CREATE TABLE external_profession_plan_audit_events (id UUID PRIMARY KEY, plan_id UUID NOT NULL REFERENCES external_profession_plans(id) ON DELETE RESTRICT, plan_version_id UUID REFERENCES external_profession_plan_versions(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, event_type VARCHAR(40) NOT NULL, actor_id VARCHAR(120) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_profession_plan_audit_scope ON external_profession_plan_audit_events(tenant_id,client_id,plan_id,created_at DESC)")

def downgrade():
    for table in ('external_profession_plan_audit_events','external_profession_plan_items','external_profession_plan_sections','external_profession_plan_versions','external_profession_plans'):
        op.execute(f'DROP TABLE IF EXISTS {table}')
