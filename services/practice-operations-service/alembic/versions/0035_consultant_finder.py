"""P35 public consultant finder governance and safe analytics."""
from alembic import op
revision="0035_consultant_finder";down_revision="0034_marketplace_shortlist";branch_labels=None;depends_on=None
def upgrade():
 op.execute("""CREATE TABLE external_marketplace_finder_config(id UUID PRIMARY KEY,config_key VARCHAR(80) UNIQUE NOT NULL,config JSONB NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,updated_by VARCHAR(120),updated_at TIMESTAMPTZ NOT NULL)""")
 op.execute("""CREATE TABLE external_marketplace_finder_events(id UUID PRIMARY KEY,profile_id UUID REFERENCES external_consultant_public_profiles(id) ON DELETE SET NULL,event_type VARCHAR(40) NOT NULL,step VARCHAR(40),support_area VARCHAR(80),created_at TIMESTAMPTZ NOT NULL,CONSTRAINT ck_finder_event CHECK(event_type IN ('FINDER_STARTED','FINDER_STEP_COMPLETED','FINDER_COMPLETED','FINDER_RESULT_VIEW','FINDER_PROFILE_CLICK','FINDER_SAVE','FINDER_COMPARE','FINDER_ENROL_CLICK','FINDER_BOOK_CLICK')))""")
 op.execute("CREATE INDEX ix_finder_events_analytics ON external_marketplace_finder_events(event_type,profile_id,created_at DESC)")
def downgrade():raise RuntimeError("Consultant finder is expand-only")
