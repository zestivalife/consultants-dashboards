from pathlib import Path

import pytest

from app.smart_intake import (FIELD_REGISTRY, InformationRequestCreate,
                              InformationRequestPatch, resolve_completeness,
                              scoped_patch)

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
