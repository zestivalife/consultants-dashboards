from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_consultant_multi_diet_plan_api_is_external_only_and_versioned():
    source = (ROOT / "app/main.py").read_text()
    for route in (
        'clients/{client_id}/diet-plans', 'diet-plans/{plan_id}',
        'diet-plans/{plan_id}/draft', 'diet-plans/{plan_id}/review',
        'diet-plans/{plan_id}/publish', 'diet-plans/{plan_id}/options/{option_id}',
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
    assert "Submit for review" not in component
    assert "Approve exact version" in component
    assert "Publish approved version" in component
    assert "expected_version: refreshed.plan.current_version" in component

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

def test_legacy_draft_save_discards_frontend_nutrition_and_re_resolves_every_option():
    source = (ROOT / "app/main.py").read_text()
    save = source[source.index("async def save_diet_plan"):source.index('@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/review")')]
    assert "_legacy_governed_option(item)" in save
    assert "await _resolve_governed_option" in save
    assert '"external_consultant_diet_draft"' in save
    assert 'options.append({**resolved' in save
    assert 'actual_calories=sum(float((item.get("nutrition") or {}).get("kcal") or 0) for item in options)' in save
    assert 'for item in body.options if item.get("selected",True)' not in save
    assert "FOR UPDATE" in save and "current_version=:expected" in save
    assert '"calculation_authority":"FITEATSY_GOVERNED_COMMON_FOOD"' in save
