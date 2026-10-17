from pathlib import Path

import pytest

from app.profession_intake import IntakeTokenError, issue_token, token_hash, validate_token

ROOT = Path(__file__).parents[1]
SCOPE = dict(tenant_id="tenant-a", client_id="client-a", intake_instance_id="11111111-1111-1111-1111-111111111111", profession_code="PSYCHOLOGIST", template_version_id="22222222-2222-2222-2222-222222222222")


def test_profession_token_is_signed_scoped_action_limited_and_hashable():
    token = issue_token(secret="test-secret", expires_at=2000, now=1000, **SCOPE)
    claims = validate_token(token, secret="test-secret", required_action="SAVE", now=1001)
    assert claims.tenant_id == "tenant-a"
    assert claims.client_id == "client-a"
    assert claims.intake_instance_id == SCOPE["intake_instance_id"]
    assert claims.profession_code == "PSYCHOLOGIST"
    assert claims.template_version_id == SCOPE["template_version_id"]
    assert len(token_hash(token)) == 64


@pytest.mark.parametrize("mutation", ["secret", "expiry", "action", "profession"])
def test_profession_token_fails_closed(mutation):
    kwargs = {**SCOPE, "secret":"test-secret", "expires_at":2000, "now":1000}
    if mutation == "profession": kwargs["profession_code"] = "UNKNOWN"
    if mutation == "action": kwargs["allowed_actions"] = ("READ",)
    if mutation == "profession":
        with pytest.raises(IntakeTokenError): issue_token(**kwargs)
        return
    token = issue_token(**kwargs)
    with pytest.raises(IntakeTokenError):
        validate_token(token, secret="wrong" if mutation=="secret" else "test-secret", required_action="SAVE", now=2001 if mutation=="expiry" else 1001)


def test_migration_is_additive_external_only_and_tenant_scoped():
    source=(ROOT/"alembic/versions/0004_profession_p1.py").read_text()
    tables=("external_profession_profiles","external_profession_capability_profiles","external_intake_template_versions","external_intake_template_sections","external_intake_template_questions","external_client_intake_instances","external_client_intake_answers","external_client_intake_custom_questions","external_client_intake_review_events","external_client_intake_audit_events")
    for table in tables: assert f"CREATE TABLE {table}" in source
    assert "ALTER TABLE" not in source
    assert "practice_tenant_configuration" not in source
    assert "diet" not in source.lower()


def test_public_routes_verify_db_scope_and_legacy_intake_is_untouched():
    source=(ROOT/"app/main.py").read_text()
    assert '"/api/v1/profession-intake/{token}"' in source
    assert "token_hash=:token_hash" in source
    assert "tenant_id=:tenant_id AND client_id=:client_id" in source
    assert "/v1/external/intake" not in source
    assert "USE_EXISTING_DIETITIAN_INTAKE" in source
