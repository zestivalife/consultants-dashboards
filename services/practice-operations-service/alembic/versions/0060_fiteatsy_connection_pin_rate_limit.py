"""Persist per-user Consultant Connection PIN attempt throttling."""
from alembic import op

revision = "0060_fit_pin_rate_limit"
down_revision = "0059_fit_appointment_links"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_fiteatsy_pin_attempt_limits (
      fiteatsy_user_id VARCHAR(120) PRIMARY KEY,
      window_started_at TIMESTAMPTZ NOT NULL,
      attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
      locked_until TIMESTAMPTZ,
      updated_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_ext_fit_pin_attempt_locked ON external_fiteatsy_pin_attempt_limits(locked_until) WHERE locked_until IS NOT NULL")


def downgrade():
    raise RuntimeError("0060_fit_pin_rate_limit retains security audit state and cannot be downgraded")
