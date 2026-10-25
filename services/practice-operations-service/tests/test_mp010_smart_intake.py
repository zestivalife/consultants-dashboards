from pathlib import Path

import pytest

from app.smart_intake import (FIELD_REGISTRY, InformationRequestCreate,
                              InformationRequestPatch, resolve_completeness,
                              resolve_assessment, scoped_patch)

ROOT=Path(__file__).parents[1]


def complete():
    return {
        "nutrition":{"dietPreference":"VEGETARIAN","mealsPerDay":"THREE","typicalDietaryIntake":"Typical meals","skipMeals":"NEVER","restrictions":[]},
        "allergiesFamilyHistory":{"hasAllergies":"NO"},
        "activityHydration":{"waterIntakeMl":2000},
        "conditionsSymptoms":{"conditions":["NO_KNOWN_CONDITIONS"]},
        "goals":{"goals":["WEIGHT_MANAGEMENT"]},
    }


def test_completeness_distinguishes_negative_optional_and_missing():
    result=resolve_completeness(complete())
    rows={row["field_id"]:row for row in result["fields"]}
    assert rows["allergy_status"]["status"]=="CAPTURED"
    assert rows["food_allergies"]["status"]=="NOT_APPLICABLE"
    assert rows["food_restrictions"]["status"]=="MISSING"
    assert rows["food_restrictions"]["blocks_readiness"] is False
    assert result["readiness"]=="NEEDS_CONSULTANT_REVIEW"


def test_pending_fields_and_partial_patch_never_clear_existing_values():
    result=resolve_completeness({},pending_fields={"dietary_preference"})
    rows={row["field_id"]:row for row in result["fields"]}
    assert rows["dietary_preference"]["status"]=="PENDING_CLIENT"
    original=complete();updated=scoped_patch(original,{"dietary_preference":"EGG"},{"dietary_preference"})
    assert updated["nutrition"]["dietPreference"]=="EGG"
    assert updated["goals"]==original["goals"]
    assert original["nutrition"]["dietPreference"]=="VEGETARIAN"


def test_request_scope_and_values_fail_closed():
    assert InformationRequestCreate(field_ids=["water_intake","water_intake"]).field_ids==["water_intake"]
    with pytest.raises(ValueError):InformationRequestCreate(field_ids=["consultant_notes"])
    with pytest.raises(ValueError):InformationRequestPatch(expected_version=1,values={"dietary_preference":"UNKNOWN"})
    with pytest.raises(ValueError):scoped_patch({}, {"health_goals":["A"]},{"water_intake"})


def test_external_only_migration_and_routes_are_governed():
    migration=(ROOT/"external_migrations/runner.py").read_text();main=(ROOT/"app/main.py").read_text()
    assert "external_0056_smart_intake_requests" in migration
    assert "token_hash_sha256" in migration
    assert "external_client_information_request_audit" in migration
    assert "internal_" not in migration[migration.index('ExternalMigration("external_0056_smart_intake_requests"'):migration.index("PRECONDITIONS")]
    for marker in ["INFORMATION_FIELD_OUT_OF_SCOPE","STALE_INFORMATION_REQUEST","REVIEW_SCOPE_INCOMPLETE","professional_review_required","scoped_patch"]:assert marker in main
    assert "alembic upgrade" not in main


def test_registry_maps_actual_intake_keys_and_excludes_professional_decisions():
    assert FIELD_REGISTRY["dietary_preference"]["path"]==("nutrition","dietPreference")
    assert FIELD_REGISTRY["water_intake"]["path"]==("activityHydration","waterIntakeMl")
    assert not ({"consultant_notes","daily_calories_target","daily_protein_target_g"}&set(FIELD_REGISTRY))


def test_completed_onboarding_maps_to_assessment_with_units_and_aliases():
    intake=complete();intake["nutrition"].update({"dietPreference":"NON_VEGETARIAN","restrictions":["NO_ONION_GARLIC"]})
    intake["activityHydration"]["waterIntakeMl"]=2500
    intake["goals"]={"selectedGoals":["LOSE_WEIGHT","BLOOD_SUGAR"]}
    resolved=resolve_assessment(intake)
    values=resolved["assessment_data"]
    assert values["dietary_preference"]=="NON_VEGETARIAN"
    assert values["food_restrictions"]==["NO_ONION_GARLIC"]
    assert values["water_intake"]=="2.5 L/day"
    assert values["nutrition_medical_conditions"]==["NO_KNOWN_CONDITIONS"]
    assert values["weight_management_goals"]==["LOSE_WEIGHT"]
    assert values["recovery_disease_management_goals"]==["BLOOD_SUGAR"]
    assert resolved["field_provenance"]["dietary_preference"]["source"]=="CLIENT_SUBMITTED"


def test_consultant_values_win_and_blank_defaults_never_erase_intake():
    resolved=resolve_assessment(complete(),{"dietary_preference":"VEGAN","water_intake":"3 L/day","consultant_notes":"Reviewed"},professionally_confirmed=True)
    assert resolved["assessment_data"]["dietary_preference"]=="VEGAN"
    assert resolved["assessment_data"]["meal_timing_frequency"]=="THREE"
    assert resolved["field_provenance"]["dietary_preference"]=={"source":"CONSULTANT_CONFIRMED","confirmed":True}


def test_explicit_negative_values_are_captured_not_missing():
    intake=complete();intake["allergiesFamilyHistory"]={"hasAllergies":"NOT_SURE"};intake["nutrition"]["restrictions"]=["NONE"]
    rows={row["field_id"]:row for row in resolve_completeness(intake)["fields"]}
    assert rows["allergy_status"]["status"]=="CAPTURED"
    assert rows["food_allergies"]["status"]=="NOT_APPLICABLE"
    assert rows["food_restrictions"]["status"]=="CAPTURED"


def test_legacy_single_choice_lists_do_not_crash_assessment_resolution():
    intake=complete()
    intake["allergiesFamilyHistory"]={"hasAllergies":["NO"]}
    intake["nutrition"].update({"dietPreference":["VEGETARIAN"],"skipMeals":["NEVER"]})
    values=resolve_assessment(intake)["assessment_data"]
    assert values["dietary_preference"]=="VEGETARIAN"
    assert values["allergies_intolerances"]==["NO"]
    assert values["appetite_eating_patterns"]==["NONE"]


def test_completeness_uses_legacy_goal_alias_and_structured_meal_history():
    intake=complete()
    intake["goals"]={"selectedGoals":["BLOOD_SUGAR"]}
    intake["nutrition"].pop("typicalDietaryIntake",None)
    intake["nutrition"]["breakfast"]=["POHA"]
    rows={row["field_id"]:row for row in resolve_completeness(intake)["fields"]}
    assert rows["health_goals"]["status"]=="CAPTURED"
    assert rows["typical_dietary_intake"]["status"]=="CAPTURED"


def test_selective_request_patch_updates_only_authorised_fields():
    original=complete();updated=scoped_patch(original,{"allergy_status":"NO","meal_timing_frequency":"4"},{"allergy_status","meal_timing_frequency"})
    assert updated["allergiesFamilyHistory"]["hasAllergies"]=="NO"
    assert updated["nutrition"]["mealsPerDay"]=="4"
    assert updated["nutrition"]["dietPreference"]==original["nutrition"]["dietPreference"]
