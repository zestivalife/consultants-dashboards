"""P33 marketplace homepage showcase (External-only, expand-only)."""
from alembic import op

revision="0033_marketplace_home_showcase";down_revision="0032_consultant_command_centre";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_consultant_homepage_features(
      profile_id UUID PRIMARY KEY REFERENCES external_consultant_public_profiles(id) ON DELETE CASCADE,
      tenant_id VARCHAR(80) NOT NULL,featured_on_homepage BOOLEAN NOT NULL DEFAULT FALSE,
      featured_rank INTEGER,featured_from TIMESTAMPTZ,featured_until TIMESTAMPTZ,
      featured_by VARCHAR(120),featured_at TIMESTAMPTZ,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_homepage_feature_rank CHECK(featured_rank IS NULL OR featured_rank>0),
      CONSTRAINT ck_homepage_feature_window CHECK(featured_until IS NULL OR featured_from IS NULL OR featured_until>featured_from))
    """)
    op.execute("CREATE INDEX ix_homepage_feature_eligible ON external_consultant_homepage_features(featured_on_homepage,featured_rank,featured_from,featured_until)")
    op.execute("""CREATE TABLE external_marketplace_homepage_events(
      id UUID PRIMARY KEY,profile_id UUID REFERENCES external_consultant_public_profiles(id) ON DELETE SET NULL,
      tenant_id VARCHAR(80),event_type VARCHAR(50) NOT NULL,profession_code VARCHAR(80),
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_homepage_event_type CHECK(event_type IN ('HOMEPAGE_CONSULTANT_IMPRESSION','HOMEPAGE_CONSULTANT_VIEW_CLICK','HOMEPAGE_ENROL_CLICK','HOMEPAGE_DIRECTORY_CLICK','HOMEPAGE_PROFESSION_CLICK')))""")
    op.execute("CREATE INDEX ix_homepage_events_analytics ON external_marketplace_homepage_events(profile_id,event_type,created_at DESC)")

def downgrade():
    raise RuntimeError("Marketplace homepage showcase is expand-only")
