import pytest

from app.diet_chart_entitlements import (
    DietChartEligibility,
    diet_chart_authoring_enabled,
    diet_chart_eligibility,
    effective_diet_chart_capabilities,
)


@pytest.mark.parametrize("profession", [
    "DIETITIAN", "NUTRITIONIST", "HEALTH_COACH", "WELLNESS_COACH",
    "FITNESS_TRAINER", "DIABETES_EDUCATOR", "WOMENS_HEALTH_PRACTITIONER",
    "LIFESTYLE_MEDICINE_PRACTITIONER", "DOCTOR_PHYSICIAN", "WELLNESS_CONSULTANT",
    "CLINICAL_NUTRITIONIST", "SPORTS_NUTRITIONIST",
])
def test_enabled_professions_receive_standard_diet_authoring(profession):
    assert diet_chart_eligibility(profession) == DietChartEligibility.ENABLED
    assert diet_chart_authoring_enabled(profession, set())


@pytest.mark.parametrize("profession", ["PHYSIOTHERAPIST", "YOGA_MEDITATION_COACH", "OTHER"])
def test_optional_professions_require_explicit_grant_and_support_revocation(profession):
    assert diet_chart_eligibility(profession) == DietChartEligibility.OPTIONAL
    assert not diet_chart_authoring_enabled(profession, set())
    assert diet_chart_authoring_enabled(profession, {"DIET_PLAN"})
    assert not diet_chart_authoring_enabled(profession, effective_diet_chart_capabilities(profession, set()))


@pytest.mark.parametrize("profession", [
    "PSYCHOLOGIST", "COUNSELLOR", "MENTOR", "BEHAVIOURAL_THERAPIST",
    "OCCUPATIONAL_THERAPIST", "MENTAL_WELLNESS_THERAPIST",
])
def test_disabled_professions_cannot_be_enabled_by_generic_capability(profession):
    assert diet_chart_eligibility(profession) == DietChartEligibility.DISABLED
    assert not diet_chart_authoring_enabled(profession, {"DIET_PLAN", "DIET_PLAN_AUTHORING"})


def test_unknown_profession_fails_closed():
    assert diet_chart_eligibility("UNMAPPED_NEW_PROFESSION") is None
    assert not diet_chart_authoring_enabled("UNMAPPED_NEW_PROFESSION", {"DIET_PLAN"})
