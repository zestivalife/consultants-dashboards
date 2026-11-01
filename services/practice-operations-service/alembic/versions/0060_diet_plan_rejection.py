"""Add an explicit terminal rejection state to the Diet Plan review workflow."""
from alembic import op

revision = "0060_diet_rejection"
down_revision = "0059_ext_measurements"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE external_profession_plans DROP CONSTRAINT ck_external_profession_plan_status")
    op.execute("ALTER TABLE external_profession_plans ADD CONSTRAINT ck_external_profession_plan_status CHECK (status IN ('DRAFT','SAVED','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED','REJECTED','APPROVED','PUBLISHED','SUPERSEDED','ARCHIVED'))")
    op.execute("ALTER TABLE external_profession_plan_versions DROP CONSTRAINT ck_external_profession_plan_version_status")
    op.execute("ALTER TABLE external_profession_plan_versions ADD CONSTRAINT ck_external_profession_plan_version_status CHECK (status IN ('DRAFT','SAVED','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED','REJECTED','APPROVED','PUBLISHED','SUPERSEDED'))")


def downgrade():
    raise RuntimeError("Diet Plan review history is expand-only")
