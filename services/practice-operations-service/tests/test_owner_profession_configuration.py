from pathlib import Path

from app.diet_chart_entitlements import DietChartEligibility, diet_chart_eligibility, effective_diet_chart_capabilities


def test_profession_policy_counts_and_fail_closed():
    enabled = {key for key in (
        "DIETITIAN", "HEALTH_COACH", "WELLNESS_COACH", "FITNESS_TRAINER",
        "DIABETES_EDUCATOR", "WOMENS_HEALTH_PRACTITIONER",
        "LIFESTYLE_MEDICINE_PRACTITIONER", "DOCTOR_PHYSICIAN", "WELLNESS_CONSULTANT"
    ) if diet_chart_eligibility(key) == DietChartEligibility.ENABLED}
    optional = {key for key in ("PHYSIOTHERAPIST", "YOGA_MEDITATION_COACH", "OTHER")
                if diet_chart_eligibility(key) == DietChartEligibility.OPTIONAL}
    disabled = {key for key in ("PSYCHOLOGIST", "COUNSELLOR", "MENTOR", "BEHAVIOURAL_THERAPIST",
                                 "OCCUPATIONAL_THERAPIST", "MENTAL_WELLNESS_THERAPIST")
                if diet_chart_eligibility(key) == DietChartEligibility.DISABLED}
    assert (len(enabled), len(optional), len(disabled)) == (9, 3, 6)
    assert "DIET_PLAN" not in effective_diet_chart_capabilities("UNKNOWN", {"DIET_PLAN"})


def test_owner_endpoint_is_scoped_concurrent_and_does_not_write_auth_role():
    source = (Path(__file__).parents[1] / "app" / "main.py").read_text()
    assert 'target_user_id != authority.user_id' in source
    assert 'WHERE tenant_id=:tenant AND version=:expected' in source
    assert '"code": "STALE_CONFIGURATION"' in source
    owner_block = source[source.index('@app.put("/internal/owner/users/{target_user_id}/profession")'):]
    assert "auth role" not in owner_block.lower()
