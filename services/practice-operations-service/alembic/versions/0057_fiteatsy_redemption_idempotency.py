"""Replay-safe Fiteatsy invitation redemption (additive only)."""
from alembic import op

revision = "0057_fit_redeem_idempotency"
down_revision = "0056_fiteatsy_connections"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE external_fiteatsy_connection_invitations ADD COLUMN redemption_idempotency_key UUID")
    op.execute("CREATE UNIQUE INDEX uq_ext_fit_redemption_replay ON external_fiteatsy_connection_invitations(redeemed_by_fiteatsy_user_id, redemption_idempotency_key) WHERE redemption_idempotency_key IS NOT NULL")


def downgrade():
    raise RuntimeError("External Fiteatsy connection persistence is expand-only")
