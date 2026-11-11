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
    assert "current completed Nutrition Assessment" not in publish
    assert "readiness_advisory" in publish
    assert "DIET_PLAN_CONSENT_REQUIRED" in publish
    assert "DIET_PLAN_GOVERNANCE_INVALID" in publish

    save = source.split('async def save_diet_plan', 1)[1].split('async def review_diet_plan', 1)[0]
    assert 'plan["status"] in {"APPROVED","PUBLISHED","ARCHIVED"}' in save
    assert 'if not body.options and not target_update_requested:return error(request,422,"DIET_PLAN_CONTENT_REQUIRED"' in save
    assert 'existing_options=[] if submitted else await _diet_options_for_version' in save

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
    assert "Publish to Client App" in component
    assert "Approve exact version" in component
    assert "DIET_PLAN_VERSION_IMMUTABLE" in (ROOT / "app/main.py").read_text()
    assert "not a clinical approval" not in component

def test_client_360_uses_only_the_multi_plan_authoring_workspace():
    component = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalClient360.jsx").read_text()
    active = component.split("export function ExternalClient360", 1)[1].split("function LegacyExternalDietPlan", 1)[0]
    assert "ExternalMultiDietPlan" in active
    assert "Open Diet Plans" in active
    for legacy_token in (
        "LegacyExternalDietPlan",
        "getExternalDietPlan",
        "sharePublishedPlan",
        "CommonFoodPlanEditor",
        "ExternalDietPlanHistory",
    ):
        assert legacy_token not in active


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


def test_published_projection_pdf_and_whatsapp_preserve_authority_boundaries():
    source = (ROOT / "app/main.py").read_text()
    component = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalMultiDietPlan.jsx").read_text()
    api = (ROOT.parents[1] / "nuetra-frontend/lib/practiceOperationsApi.js").read_text()
    for invariant in (
        '"contractVersion":"EXTERNAL_DIET_PLAN_V1"',
        '"calculationAuthority":"FITEATSY_GOVERNED_COMMON_FOOD"',
        'item.get("calculationStatus")!="AUTHORITATIVELY_RESOLVED"',
        '"fiteatsy.external.diet.write"',
        '"fiteatsy.external.diet.select"',
        '"externalPlanId":str(plan["id"])',
        "external_fiteatsy_active_plan_selections",
        "status='SUPERSEDED'",
    ):
        assert invariant in source
    assert 'format:str=Query("DOCX",pattern="^(PDF|DOCX)$")' in source
    assert 'build_diet_pdf(snapshot,logo_path) if is_pdf else build_diet_docx(snapshot,logo_path)' in source
    assert 'plan["status"] not in {"APPROVED","PUBLISHED"}' in source
    assert 'body.intent == "SHARE_PUBLISHED_PLAN"' in source
    assert "PUBLISHED_DIET_PLAN_NOT_FOUND" in source
    assert "DIET_PLAN_CONSENT_REQUIRED" in source
    assert "Download PDF" in component and "Share via WhatsApp" in component
    assert "openWhatsApp" in component and "shareable_type:'PUBLISHED_DIET_PLAN'" in component
    assert "format='DOCX'" in api and "application/pdf" in api


def test_mobile_nutrition_adapter_preserves_seven_meals_and_authoritative_values():
    from app.main import _fiteatsy_nutrition_content

    plan = {
        "id": "plan-1", "tenant_id": "tenant-1", "client_id": "client-1",
        "authorised_consultant_id": "consultant-1", "title": "Reviewed plan",
        "daily_calories_target": 1800, "daily_protein_target_g": 100,
    }
    option = {
        "combinationId": "option-1", "mealHead": "BREAKFAST", "clientTitle": "Poha and curd",
        "humanServingSummary": "1 bowl", "calculationStatus": "AUTHORITATIVELY_RESOLVED",
        "nutrition": {"kcal": 320, "protein": 14, "carbs": 48, "fat": 8, "fibre": 6},
        "components": [{"componentId": "component-1", "foodId": "food-1", "foodDisplayNameSnapshot": "Poha",
            "servingDisplayNameSnapshot": "1 bowl", "label": "1 bowl", "grams": 100,
            "nutrition": {"kcal": 320, "protein": 14, "carbs": 48, "fat": 8, "fibre": 6}}],
    }
    content = _fiteatsy_nutrition_content(plan, [option])
    assert list(content["mealPlan"]) == ["earlyMorning", "breakfast", "midMorningSnack", "lunch", "eveningSnack", "dinner", "bedtimeNutrition"]
    rendered = content["mealPlan"]["breakfast"]["options"][0]
    assert rendered["approxKcal"] == 320 and rendered["proteinGrams"] == 14
    assert rendered["components"][0]["foodId"] == "food-1"
    assert rendered["components"][0]["calories"] == 320


def test_fiteatsy_publication_uses_canonical_utc_z_timestamp():
    source = (ROOT / "app/main.py").read_text()
    delivery = source[source.index("async def _deliver_diet_plan_to_fiteatsy"):source.index("async def _active_diet_connection")]
    assert 'published_at.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")' in delivery
    assert '"publishedAtISO":published_at.isoformat()' not in delivery

def test_energy_estimate_delegates_to_fiteatsy_and_targets_are_immutable_snapshot_data():
    source = (ROOT / "app/main.py").read_text()
    contracts = (ROOT / "app/contracts.py").read_text()
    estimate = source[source.index('async def estimate_diet_plan_energy'):source.index('async def _resolve_governed_option')]
    assert "fiteatsy.external.health.calculate" in estimate
    assert "external_consultant_health_calculation" in estimate
    assert "consented_scopes ? 'PROFILE'" in source
    assert "consented_scopes ? 'MEASUREMENTS'" in source
    assert "FITEATSY_HEALTH_CALCULATION_CONTRACT_INVALID" in estimate
    assert "class DietEnergyEstimateRequest" in contracts
    for field in ("daily_carbohydrate_target_g", "daily_fat_target_g", "daily_fibre_target_g", "target_methodology", "calculation_provenance"):
        assert field in contracts
        assert field in source
    create = source[source.index('async def create_diet_plan'):source.index('@app.get("/api/v1/practice-operations/diet-plans/{plan_id}")')]
    save = source[source.index('async def save_diet_plan'):source.index('@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/review")')]
    assert '"target_methodology":body.target_methodology' in create
    assert "previous_snapshot" in save and "{**previous_snapshot" in save
    assert "10 *" not in estimate and "activityMultiplier" not in estimate

def test_legacy_draft_save_discards_frontend_nutrition_and_re_resolves_every_option():
    source = (ROOT / "app/main.py").read_text()
    save = source[source.index("async def save_diet_plan"):source.index('@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/review")')]
    assert "_legacy_governed_option(item)" in save
    assert "await _resolve_governed_option" in save
    assert '"external_consultant_diet_option"' in save
    assert '"external_consultant_diet_draft"' not in save
    assert 'options.append({**resolved' in save
    assert 'actual_calories=sum(float((item.get("nutrition") or {}).get("kcal") or 0) for item in options)' in save
    assert 'for item in body.options if item.get("selected",True)' not in save
    assert "FOR UPDATE" in save and "current_version=:expected" in save
    assert '"calculation_authority":"FITEATSY_GOVERNED_COMMON_FOOD"' in save
