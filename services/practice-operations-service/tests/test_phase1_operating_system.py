from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_phase1_schema_is_external_tenant_scoped_and_expand_only():
    source = (ROOT / "alembic/versions/0003_phase1_operating_system.py").read_text()
    for table in (
        "practice_tenant_configuration", "practice_communication_templates",
        "practice_communication_activity", "practice_notifications",
        "practice_timeline_events",
    ):
        assert table in source
    assert source.count("tenant_id VARCHAR(80)") == 5
    assert "Internal" not in source
    assert "expand-only" in source


def test_phase1_capability_and_profession_contracts_are_governed():
    source = (ROOT / "app/main.py").read_text()
    for value in (
        "ALL_CAPABILITIES", "PROFESSION_DEFAULTS", "TERMINOLOGY",
        "CAPABILITY_NOT_ENABLED", "PRACTICE_ADMIN_REQUIRED",
        "EXTERNAL_PRACTICE_SCOPE_REQUIRED",
    ):
        assert value in source
    assert '"PSYCHOLOGIST"' in source
    assert '"PHYSIOTHERAPIST"' in source
    assert '"HEALTH_COACH"' in source
    assert 'if resource == "configuration"' in source


def test_whatsapp_activity_never_claims_delivery():
    source = (ROOT / "app/main.py").read_text()
    assert "WHATSAPP_OPENED" in source
    assert "WhatsApp opened for" in source
    assert "MESSAGE_SENT" not in source
    assert "DELIVERED" not in source
    assert "DRAFT_NOT_SHAREABLE" in source


def test_onboarding_notification_and_timeline_are_idempotent():
    migration = (ROOT / "alembic/versions/0003_phase1_operating_system.py").read_text()
    source = (ROOT / "app/main.py").read_text()
    assert "uq_practice_onboarding_complete_notification" in migration
    assert "ON CONFLICT (tenant_id,event_type,client_id)" in source
    assert '"actions":["VIEW_CLIENT","WHATSAPP"]' in source
    assert "practice_timeline_events" in source
