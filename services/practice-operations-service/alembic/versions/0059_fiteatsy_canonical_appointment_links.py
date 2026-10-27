"""Link Fiteatsy projections to the authoritative scheduler."""
from alembic import op

revision = "0059_fit_appointment_links"
down_revision = "0058_fit_active_plan"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
      CREATE TABLE external_fiteatsy_appointment_links (
        id UUID PRIMARY KEY,
        connection_id UUID NOT NULL REFERENCES external_fiteatsy_connections(id) ON DELETE RESTRICT,
        tenant_id VARCHAR(80) NOT NULL,
        appointment_id UUID NOT NULL REFERENCES external_scheduled_appointments(id) ON DELETE RESTRICT,
        idempotency_key VARCHAR(120) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        CONSTRAINT uq_ext_fit_appointment_link UNIQUE(connection_id, appointment_id),
        CONSTRAINT uq_ext_fit_appointment_link_idempotency UNIQUE(connection_id, idempotency_key)
      )
    """)
    op.execute("CREATE INDEX ix_ext_fit_appointment_link_connection ON external_fiteatsy_appointment_links(connection_id, created_at DESC)")


def downgrade():
    raise RuntimeError("External Fiteatsy canonical appointment links are expand-only")
