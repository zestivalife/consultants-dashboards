from pathlib import Path

from app.p37 import project_readiness, resolve_requirements

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app/main.py").read_text()
MIGRATION = (ROOT / "alembic/versions/0037_pre_consultation_onboarding.py").read_text()


def test_migration_is_additive_external_only_and_linear():
    assert 'down_revision = "0036_marketplace_booking"' in MIGRATION
    assert "external_preconsultation_checklists" in MIGRATION
    assert "external_preconsultation_events" in MIGRATION
    assert "ALTER TABLE" not in MIGRATION
    assert "ZESTIVA_INTERNAL" not in MIGRATION


def test_profession_capability_drives_assessment_and_optional_documents_do_not_block():
    requirements = resolve_requirements("PSYCHOLOGIST", ["ASSESSMENTS", "CLIENT_PORTAL"])
    assert requirements["ASSESSMENT"]["required"] is True
    assert requirements["DOCUMENTS"]["required"] is False
    facts = {key: {"state": "COMPLETE"} for key in ("PROFILE", "INTAKE", "CONSENT", "ASSESSMENT", "APPOINTMENT", "PORTAL")}
    result = project_readiness(requirements, facts)
    assert result["readyForConsultation"] is True
    assert result["readinessPercent"] == 100


def test_required_document_is_an_explicit_readiness_blocker():
    requirements = resolve_requirements("HEALTH_COACH", ["CLIENT_PORTAL"], {"DOCUMENTS": {"required": True, "requests": ["REFERRAL"]}})
    facts = {key: {"state": "COMPLETE"} for key in ("PROFILE", "INTAKE", "CONSENT", "APPOINTMENT", "PORTAL")}
    result = project_readiness(requirements, facts)
    assert result["readyForConsultation"] is False
    assert "REQUIRED_DOCUMENT_PENDING" in result["blockers"]


def test_handoff_requires_existing_governed_conversion_and_reuses_domains():
    section = MAIN[MAIN.index('@app.post("/api/v1/practice-operations/clients/{client_id}/pre-consultation/invite"'):MAIN.index("async def _portal_scope")]
    assert "converted_client_id" in section and "GOVERNED_CLIENT_LINK_REQUIRED" in section
    for domain in ("external_form_assignments", "external_consent_records", "external_client_portal_access_grants"):
        assert domain in section
    assert "issue_portal_token" in section and "portal_token_hash" in section
    assert "INSERT INTO clients" not in section and "password_hash" not in section


def test_portal_command_centre_and_operational_analytics_are_integrated():
    for marker in ('"preConsultation": preconsultation', 'section="preconsultation"', '"OPERATIONAL_NOT_CLINICAL"', 'APPOINTMENT_APPROACHING_ONBOARDING_INCOMPLETE'):
        assert marker in MAIN
