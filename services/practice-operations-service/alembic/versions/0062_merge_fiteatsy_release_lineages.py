"""Merge the production directory and release diet-plan migration lineages.

This revision intentionally performs no DDL. Alembic upgrades each missing
additive branch before recording this shared head.
"""


revision = "0062_merge_release_heads"
down_revision = ("0061_fiteatsy_directory", "0060_diet_rejection")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    raise RuntimeError("The production/release lineage merge is expand-only")
