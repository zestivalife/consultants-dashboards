"""P26 one-tenant multi-location practice model."""
from alembic import op
revision="0026_multi_location";down_revision="0025_communication_centre";branch_labels=None;depends_on=None
def upgrade():
    op.execute("""CREATE TABLE external_practice_locations(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,code VARCHAR(80) NOT NULL,name VARCHAR(240) NOT NULL,address JSONB NOT NULL DEFAULT '{}'::jsonb,timezone VARCHAR(80) NOT NULL,phone VARCHAR(60),active BOOLEAN NOT NULL DEFAULT TRUE,created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,code))""")
    op.execute("""CREATE TABLE external_location_resource_links(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,location_id UUID NOT NULL REFERENCES external_practice_locations(id),resource_type VARCHAR(30) NOT NULL,resource_id VARCHAR(120) NOT NULL,primary_location BOOLEAN NOT NULL DEFAULT FALSE,created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,CONSTRAINT ck_location_resource_type CHECK(resource_type IN ('TEAM_MEMBER','CLIENT','APPOINTMENT','SERVICE','INVOICE','LEAD')),UNIQUE(tenant_id,resource_type,resource_id,location_id))""")
    op.execute("""CREATE TABLE external_location_audit_events(id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,location_id UUID NOT NULL REFERENCES external_practice_locations(id),event_type VARCHAR(40) NOT NULL,actor_id VARCHAR(120) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_location_resources ON external_location_resource_links(tenant_id,location_id,resource_type)")
def downgrade():raise RuntimeError("Multi-location is expand-only")
