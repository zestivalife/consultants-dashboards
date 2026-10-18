"""P32 External Consultant command-centre visit state (expand-only)."""
from alembic import op

revision="0032_consultant_command_centre";down_revision="0031_consultant_marketplace";branch_labels=None;depends_on=None


def upgrade():
    op.execute("""CREATE TABLE external_consultant_dashboard_state(
      tenant_id VARCHAR(80) NOT NULL,user_id VARCHAR(120) NOT NULL,
      dashboard_last_seen_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY(tenant_id,user_id)
    )""")
    op.execute("CREATE INDEX ix_external_dashboard_state_seen ON external_consultant_dashboard_state(tenant_id,dashboard_last_seen_at DESC)")


def downgrade():
    raise RuntimeError("Consultant command-centre state is expand-only")
