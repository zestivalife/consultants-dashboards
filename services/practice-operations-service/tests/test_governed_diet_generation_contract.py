from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generation_is_assignment_and_consent_guarded_and_uses_fiteatsy_authority():
    source = (ROOT / "app" / "main.py").read_text()
    endpoint = source[source.index('@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/generate-options")'):]
    endpoint = endpoint[:endpoint.index("def _legacy_governed_option")]

    assert '_diet_plan_assignment_guard(request,db,ctx,plan,"PLAN_EDIT")' in endpoint
    assert '_active_diet_connection(db,ctx,plan["client_id"])' in endpoint
    assert 'fiteatsy.external.diet.generate' in endpoint
    assert 'external_consultant_diet_generation' in endpoint
    assert '/common-food/generate' in endpoint
    assert 'FITEATSY_GENERATOR_CONTRACT_INVALID' in endpoint


def test_generation_uses_saved_version_targets_and_does_not_persist_options():
    source = (ROOT / "app" / "main.py").read_text()
    endpoint = source[source.index('@app.post("/api/v1/practice-operations/diet-plans/{plan_id}/generate-options")'):]
    endpoint = endpoint[:endpoint.index("def _legacy_governed_option")]

    assert 'projection=await _diet_plan_projection(db,plan)' in endpoint
    assert 'projected_plan["daily_carbohydrate_target_g"]' in endpoint
    assert 'projected_plan["daily_fat_target_g"]' in endpoint
    assert 'projected_plan["daily_fibre_target_g"]' in endpoint
    assert "INSERT INTO external_profession_plan" not in endpoint
    assert "UPDATE external_profession_plan" not in endpoint
    assert "await db.commit()" not in endpoint
