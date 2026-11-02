from __future__ import annotations

from enum import Enum


class DietChartEligibility(str, Enum):
    ENABLED = "ENABLED"
    OPTIONAL = "OPTIONAL"
    DISABLED = "DISABLED"


DIET_CHART_ELIGIBILITY = {
    "DIETITIAN": DietChartEligibility.ENABLED,
    "NUTRITIONIST": DietChartEligibility.ENABLED,
    "CLINICAL_NUTRITIONIST": DietChartEligibility.ENABLED,
    "SPORTS_NUTRITIONIST": DietChartEligibility.ENABLED,
    "HEALTH_COACH": DietChartEligibility.ENABLED,
    "WELLNESS_COACH": DietChartEligibility.ENABLED,
    "PSYCHOLOGIST": DietChartEligibility.DISABLED,
    "COUNSELLOR": DietChartEligibility.DISABLED,
    "PHYSIOTHERAPIST": DietChartEligibility.OPTIONAL,
    "FITNESS_TRAINER": DietChartEligibility.ENABLED,
    "YOGA_MEDITATION_COACH": DietChartEligibility.OPTIONAL,
    "DIABETES_EDUCATOR": DietChartEligibility.ENABLED,
    "WOMENS_HEALTH_PRACTITIONER": DietChartEligibility.ENABLED,
    "LIFESTYLE_MEDICINE_PRACTITIONER": DietChartEligibility.ENABLED,
    "MENTOR": DietChartEligibility.DISABLED,
    "DOCTOR_PHYSICIAN": DietChartEligibility.ENABLED,
    "OTHER": DietChartEligibility.OPTIONAL,
    "WELLNESS_CONSULTANT": DietChartEligibility.ENABLED,
    "BEHAVIOURAL_THERAPIST": DietChartEligibility.DISABLED,
    "OCCUPATIONAL_THERAPIST": DietChartEligibility.DISABLED,
    "MENTAL_WELLNESS_THERAPIST": DietChartEligibility.DISABLED,
}


def diet_chart_eligibility(profession: str) -> DietChartEligibility | None:
    return DIET_CHART_ELIGIBILITY.get(profession)


def effective_diet_chart_capabilities(profession: str, capabilities: set[str]) -> set[str]:
    """Apply product policy to stored grants; unknown professions fail closed."""
    effective = set(capabilities)
    eligibility = diet_chart_eligibility(profession)
    if eligibility == DietChartEligibility.ENABLED:
        effective.add("DIET_PLAN")
    elif eligibility != DietChartEligibility.OPTIONAL:
        effective.discard("DIET_PLAN")
        effective.discard("DIET_PLAN_AUTHORING")
    return effective


def diet_chart_authoring_enabled(profession: str, capabilities: set[str]) -> bool:
    return "DIET_PLAN" in effective_diet_chart_capabilities(profession, capabilities)
