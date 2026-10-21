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
        "daily_protein_target_g", "STALE_WRITE", "SENIOR_REVIEW_REQUIRED",
        "DIET_PLAN_APPROVAL_REQUIRED", "nutrition_snapshot",
    ):
        assert token in source
    assert "plan_type='DIET_PLAN'" in source

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
