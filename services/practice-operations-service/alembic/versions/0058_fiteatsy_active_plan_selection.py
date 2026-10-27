"""One explicit active external diet plan per Fiteatsy user."""
from alembic import op

revision = "0058_fit_active_plan"
down_revision = "0057_fit_redeem_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
      CREATE TABLE external_fiteatsy_active_plan_selections (
        fiteatsy_user_id VARCHAR(120) PRIMARY KEY,
        publication_id UUID NOT NULL REFERENCES external_fiteatsy_plan_publications(id),
        selected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    """)
    op.execute("CREATE INDEX ix_ext_fit_active_plan_publication ON external_fiteatsy_active_plan_selections(publication_id)")


def downgrade():
    raise RuntimeError("External Fiteatsy connection persistence is expand-only")
