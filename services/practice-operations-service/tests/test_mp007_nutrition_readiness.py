from pathlib import Path

from app.nutrition_foundation import AssessmentSource, NutritionProfile, diet_plan_readiness

ROOT = Path(__file__).parents[1]


def source(kind):
    return AssessmentSource(source_type=kind, source_id=f"{kind.lower()}-1", source_version="1")


def complete_profile(preference="VEGETARIAN"):
    return NutritionProfile(
        dietary_preference=preference,
        meal_timing_frequency="Three meals and one snack",
        typical_dietary_intake="Source-backed intake recorded",
        appetite_eating_patterns="Stable",
        water_intake="2 litres",
    )


def test_server_readiness_is_explicit_and_review_governed():
    sources=[source("ALLERGIES"),source("MEDICAL_HISTORY"),source("MEASUREMENT")]
    assert diet_plan_readiness(complete_profile(),sources,workflow_status="SUBMITTED")["outcome"] == "NEEDS_REVIEW"
    ready=diet_plan_readiness(complete_profile(),sources,workflow_status="REVIEWED")
    assert ready["outcome"] == "READY"
    assert ready["clinical_safety_guarantee"] is False


def test_incomplete_and_unsupported_vegan_fail_closed():
    assert diet_plan_readiness(NutritionProfile(),[],workflow_status="DRAFT")["outcome"] == "NOT_STARTED"
    incomplete=diet_plan_readiness(NutritionProfile(dietary_preference="VEGETARIAN"),[source("ALLERGIES")],workflow_status="DRAFT")
    assert incomplete["outcome"] == "INCOMPLETE"
    vegan=diet_plan_readiness(complete_profile("VEGAN"),[source("ALLERGIES"),source("MEDICAL_HISTORY")],workflow_status="REVIEWED")
    assert vegan["outcome"] == "BLOCKED"
    assert "vegan_food_engine_not_supported" in vegan["outstanding_information"]


def test_mp007_is_external_only_versioned_and_audited():
    migration=(ROOT/"alembic/versions/0055_nutrition_assessment_readiness.py").read_text()
    app=(ROOT/"app/main.py").read_text()
    assert 'down_revision = "0054_nutrition_foundation"' in migration
    assert "external_nutrition_assessment_events" in migration
    assert "ZESTIVA_INTERNAL" not in migration
    assert "Fiteatsy" not in migration
    assert "STALE_NUTRITION_ASSESSMENT" in app
    assert "INVALID_NUTRITION_ASSESSMENT_TRANSITION" in app
    assert '"idempotent":current["status"]==new_status' in app
    assert 'nutrition-assessments/{assessment_id}/transition' in app
    assert "diet_plan_readiness" in app
