"""P34 public marketplace shortlist analytics (External-only, expand-only)."""
from alembic import op

revision="0034_marketplace_shortlist";down_revision="0033_marketplace_home_showcase";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_marketplace_comparison_events(
      id UUID PRIMARY KEY,profile_id UUID REFERENCES external_consultant_public_profiles(id) ON DELETE SET NULL,
      tenant_id VARCHAR(80),event_type VARCHAR(40) NOT NULL,compared_profile_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
      created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_marketplace_comparison_event CHECK(event_type IN ('CONSULTANT_SAVED','CONSULTANT_UNSAVED','COMPARISON_OPENED','COMPARE_PROFILE_CLICK','COMPARE_ENROL_CLICK')))""")
    op.execute("CREATE INDEX ix_marketplace_comparison_analytics ON external_marketplace_comparison_events(profile_id,event_type,created_at DESC)")

def downgrade():
    raise RuntimeError("Marketplace shortlist analytics is expand-only")
