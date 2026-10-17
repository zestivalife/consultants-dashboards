from pathlib import Path
import pytest
from pydantic import ValidationError
from app.schemas.people_access import ExternalQaPracticeCreateRequest
from app.schemas.auth import LoginRequest
from app.services.external_qa_practice_service import _fixture_key, _validate_qa

PROFESSIONS = (
    "DIABETES_EDUCATOR","PSYCHOLOGIST","WELLNESS_CONSULTANT","HEALTH_COACH",
    "BEHAVIOURAL_THERAPIST","OCCUPATIONAL_THERAPIST","PHYSIOTHERAPIST","MENTAL_WELLNESS_THERAPIST",
)


def body(profession="PSYCHOLOGIST", email="qa+psychologist@zestiva.test", tenant="Psychologist QA Practice"):
    return ExternalQaPracticeCreateRequest(profession_code=profession, tenant_name=tenant,
        consultant_display_name="QA Psychologist", consultant_email=email)


def test_all_and_only_governed_professions_are_accepted():
    for profession in PROFESSIONS:
        assert body(profession=profession).profession_code == profession
        assert _fixture_key(profession).startswith("external-qa-")
    with pytest.raises(ValidationError):
        body(profession="DIETITIAN")


@pytest.mark.parametrize("email,tenant", [
    ("real@example.com", "Psychologist QA Practice"),
    ("qa+psychologist@zestiva.test", "Psychologist Practice"),
])
def test_non_qa_identity_or_tenant_fails_closed(email, tenant):
    with pytest.raises(Exception):
        _validate_qa(body(email=email, tenant=tenant))


def test_governed_qa_identity_can_use_normal_login_contract():
    request = LoginRequest(email="qa+psychologist@zestiva.test", password="temporary-secret")
    assert request.email == "qa+psychologist@zestiva.test"


@pytest.mark.parametrize("email", [
    "real-user@zestiva.test",
    "qa+psychologist@example.test",
    "qa+@zestiva.test",
])
def test_login_does_not_broaden_reserved_domain_acceptance(email):
    with pytest.raises(ValidationError):
        LoginRequest(email=email, password="temporary-secret")


def test_orchestration_uses_signed_exact_scope_and_no_credential_output():
    source = Path("app/services/external_qa_practice_service.py").read_text()
    assert '"purpose": "qa_external_practice"' in source
    assert '"actor_type": "platform_owner"' in source
    assert "practice.qa.external.configure" in source
    assert "target_user_id=str(user_id)" in source
    assert "USE_GOVERNED_OWNER_PASSWORD_RESET" in source
    assert "plain_password" not in source
    assert "temporary_password" not in source


def test_downstream_failure_uses_pre_rollback_ledger_identity():
    source = Path("app/services/external_qa_practice_service.py").read_text()
    assert "ledger_id = ledger.id" in source
    assert "session.get(ExternalQaPracticeProvisioning, ledger_id)" in source
    assert "session.get(ExternalQaPracticeProvisioning, ledger.id)" not in source


def test_migration_is_additive_and_does_not_touch_normal_auth_semantics():
    source = Path("alembic/versions/e6f7a8b9c0d1_governed_external_qa_practice.py").read_text().lower()
    assert "external_qa_practice_provisioning" in source
    assert "qa.external_practice.provision" in source
    assert "governed_qa_external" in source
    for forbidden in ("jwt", "refresh_tokens", "external_signup_challenges", "password_hash"):
        assert forbidden not in source
