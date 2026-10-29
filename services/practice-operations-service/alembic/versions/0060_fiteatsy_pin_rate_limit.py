"""Persist per-user rate limits for Fiteatsy Connection PIN preview attempts."""
from alembic import op

revision = "0060_fit_pin_rate_limit"
down_revision = "0058_fit_active_plan"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_fiteatsy_pin_attempt_limits (
      fiteatsy_user_id VARCHAR(120) PRIMARY KEY,
      window_started_at TIMESTAMPTZ NOT NULL,
      attempt_count INTEGER NOT NULL DEFAULT 0,
      locked_until TIMESTAMPTZ,
      updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT external_fiteatsy_pin_attempt_limits_attempt_count_check
        CHECK (attempt_count >= 0)
    )""")
    op.execute("""CREATE INDEX ix_ext_fit_pin_attempt_locked
      ON external_fiteatsy_pin_attempt_limits(locked_until)
      WHERE locked_until IS NOT NULL""")


def downgrade():
    raise RuntimeError("External Fiteatsy PIN rate limiting is expand-only")
