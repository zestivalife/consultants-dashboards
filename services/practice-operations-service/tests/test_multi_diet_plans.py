from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_consultant_multi_diet_plan_api_is_external_only_and_versioned():
    source = (ROOT / "app/main.py").read_text()
    for route in (
        'clients/{client_id}/diet-plans', 'diet-plans/{plan_id}',
        'diet-plans/{plan_id}/draft', 'diet-plans/{plan_id}/review',
        'diet-plans/{plan_id}/publish',
    ):
        assert route in source
    for token in (
        "authorised_consultant_id", "daily_calories_target",
        "daily_protein_target_g", "STALE_WRITE",
        "CONSULTANT_AUTHORED_VALIDATED", "nutrition_snapshot",
    ):
        assert token in source
    assert "plan_type='DIET_PLAN'" in source

    publish = source.split('async def publish_diet_plan', 1)[1].split('async def _write_note_sections', 1)[0]
    assert "can_publish_independently" not in publish
    assert "DIET_PLAN_APPROVAL_REQUIRED" in publish
    assert 'plan["status"]!="APPROVED"' in publish
    assert "SENIOR_REVIEW_REQUIRED" not in publish
    assert "current completed Nutrition Assessment" in publish

    save = source.split('async def save_diet_plan', 1)[1].split('async def review_diet_plan', 1)[0]
    assert 'plan["status"] in {"APPROVED","PUBLISHED","ARCHIVED"}' in save

def test_multi_plan_migration_is_consultant_owned_and_does_not_touch_fiteatsy():
    source = (ROOT / "alembic/versions/0051_consultant_multi_diet_plans.py").read_text()
    assert "external_profession_plans" in source
    assert "external_profession_plan_versions" in source
    assert "fiteatsy" not in source.lower()
    assert "UNIQUE(tenant_id,client_id" not in source.replace(" ", "")

def test_frontend_uses_practice_operations_for_plan_writes_and_catalogue_read_only():
    component = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalMultiDietPlan.jsx").read_text()
    api = (ROOT.parents[1] / "nuetra-frontend/lib/practiceOperationsApi.js").read_text()
    for value in ("listConsultantDietPlans", "createConsultantDietPlan", "saveConsultantDietPlan", "publishConsultantDietPlan"):
        assert value in component and value in api
    assert "createExternalDietPlan" not in component
    assert "publishExternalDietPlanById" not in component
    assert "searchExternalCommonFoods" in component
    assert "GOVERNED_CATALOGUE" in component
    assert "reviewConsultantDietPlan" in component
    assert "Submit for review" not in component
    assert "Publish approved version" in component
    assert "Approve exact version" in component
    assert "DIET_PLAN_VERSION_IMMUTABLE" in (ROOT / "app/main.py").read_text()
    assert "not a clinical approval" not in component

def test_client_360_uses_only_the_multi_plan_authoring_workspace():
    component = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalClient360.jsx").read_text()
    assert "ExternalMultiDietPlan" in component
    assert "Open Diet Plans" in component
    for legacy_token in (
        "LegacyExternalDietPlan",
        "getExternalDietPlan",
        "sharePublishedPlan",
        "CommonFoodPlanEditor",
        "ExternalDietPlanHistory",
    ):
        assert legacy_token not in component


def test_governed_option_updates_are_atomic_authoritative_and_consent_scoped():
    source = (ROOT / "app/main.py").read_text()
    contracts = (ROOT / "app/contracts.py").read_text()
    frontend = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalMultiDietPlan.jsx").read_text()
    api = (ROOT.parents[1] / "nuetra-frontend/lib/practiceOperationsApi.js").read_text()
    for invariant in (
        "Idempotency-Key", "expected_version", "pg_advisory_xact_lock", "FOR UPDATE",
        "state='ACTIVE'", "consented_scopes ? 'DIET_PLANS'", "fiteatsy.external.diet.resolve",
        "external_consultant_diet_option", "AUTHORITATIVELY_RESOLVED", "OPTION_UPDATED",
        "calculation_authority", "FITEATSY_GOVERNED_COMMON_FOOD",
    ):
        assert invariant in source
    assert "class GovernedDietOptionUpdate" in contracts
    assert "updateConsultantDietPlanOption" in api and "updateConsultantDietPlanOption" in frontend
    assert "payload.components.reduce" not in frontend
    assert "nutrition:payload.components.reduce" not in frontend
