from pathlib import Path


def test_internal_configuration_is_signed_and_exact_scope_only():
    auth = Path("app/qa_delegation.py").read_text()
    route = Path("app/main.py").read_text()
    assert 'algorithms=["RS256"]' in auth
    assert 'audience=settings.qa_delegation_audience' in auth
    assert 'issuer=settings.qa_delegation_issuer' in auth
    assert '"practice.qa.external.configure"' in auth
    assert '"target_user_id"' in auth
    assert '"tenant_id"' in auth
    assert '"profession_code"' in auth
    assert '@app.put("/internal/qa/external-practice/configuration")' in route
    assert "body.profession != authority.profession_code" in route


def test_profession_configuration_reuses_authoritative_models():
    route = Path("app/main.py").read_text()
    section = route[route.index('async def configure_external_qa_practice'):route.index('def _profession_token_error')]
    assert "body.profession not in PROFESSION_DEFAULTS" in section
    assert "body.profession not in SUPPORTED_PROFESSIONS" not in section
    for table in ("practice_tenant_configuration", "external_profession_profiles", "external_profession_capability_profiles"):
        assert table in section
    assert "diet_chart_eligibility(body.profession)" in section
    assert "effective_diet_chart_capabilities(body.profession, requested)" in section
    for frozen in ("biomarker", "zestiva_internal"):
        assert frozen not in section.lower()


def test_governed_nutritionist_configuration_uses_existing_diet_plan_defaults():
    route = Path("app/main.py").read_text()
    assert '"NUTRITIONIST": {' in route
    nutritionist_defaults = route[route.index('"NUTRITIONIST": {'):route.index('"CLINICAL_NUTRITIONIST": {')]
    assert '"DIET_PLAN"' in nutritionist_defaults
