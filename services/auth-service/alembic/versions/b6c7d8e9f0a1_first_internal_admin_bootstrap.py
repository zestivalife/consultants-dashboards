"""Add replay-safe evidence for the first Internal Super Admin bootstrap."""

from alembic import op

revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"


def upgrade():
    op.execute(
        "ALTER TABLE internal_privileged_invitations "
        "ADD COLUMN IF NOT EXISTS bootstrap_authority_principal VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE internal_privileged_invitations "
        "ADD COLUMN IF NOT EXISTS bootstrap_grant_hash VARCHAR(64)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_internal_privileged_bootstrap_grant_hash "
        "ON internal_privileged_invitations (bootstrap_grant_hash) "
        "WHERE bootstrap_grant_hash IS NOT NULL"
    )


def downgrade():
    # Security/audit evidence is intentionally retained.
    pass
