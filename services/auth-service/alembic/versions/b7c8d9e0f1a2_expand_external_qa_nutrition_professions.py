"""Allow governed nutrition professions in External QA provisioning."""

from alembic import op

revision = "b7c8d9e0f1a2"
down_revision = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None

PROFESSIONS = (
    "'DIETITIAN','NUTRITIONIST','CLINICAL_NUTRITIONIST','SPORTS_NUTRITIONIST',"
    "'DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH',"
    "'BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST'"
)
LEGACY_PROFESSIONS = (
    "'DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH',"
    "'BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST'"
)


def _replace_constraint(allowed: str) -> None:
    op.drop_constraint("ck_external_qa_practice_profession", "external_qa_practice_provisioning", type_="check")
    op.create_check_constraint(
        "ck_external_qa_practice_profession",
        "external_qa_practice_provisioning",
        f"profession_code in ({allowed})",
    )


def upgrade() -> None:
    _replace_constraint(PROFESSIONS)


def downgrade() -> None:
    _replace_constraint(LEGACY_PROFESSIONS)
