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


def test_nutrition_profession_aliases_resolve_centrally_with_full_client360_capabilities():
    from app.main import PROFESSION_DEFAULTS, canonical_profession

    aliases = {
        "DIETITIAN": "DIETITIAN",
        "Dietitian": "DIETITIAN",
        "Dietician": "DIETITIAN",
        "Registered Dietitian": "DIETITIAN",
        "Nutritionist": "NUTRITIONIST",
        "Nutrition Consultant": "NUTRITIONIST",
        "Nutrition Consultant / Dietitian": "DIETITIAN",
        "DIETITIAN_NUTRITIONIST": "DIETITIAN",
        "Clinical Dietitian": "CLINICAL_NUTRITIONIST",
        "Clinical Nutritionist": "CLINICAL_NUTRITIONIST",
        "Sports Nutritionist": "SPORTS_NUTRITIONIST",
    }
    required = {"DIET_PLAN", "LAB_ANALYSIS", "BIOMARKERS", "MEASUREMENTS"}
    for alias, expected in aliases.items():
        assert canonical_profession(alias) == expected
        assert required <= PROFESSION_DEFAULTS[expected]

    assert canonical_profession("Health Coach") == "HEALTH_COACH"
    assert "DIET_PLAN" not in PROFESSION_DEFAULTS["HEALTH_COACH"]
    assert canonical_profession("Unknown clinical role") == "OTHER"


def test_whatsapp_activity_never_claims_delivery():
    source = (ROOT / "app/main.py").read_text()
    assert "WHATSAPP_OPENED" in source
    assert "WhatsApp opened for" in source
    assert "MESSAGE_SENT" not in source
    assert "DELIVERED" not in source
    assert "DRAFT_NOT_SHAREABLE" in source
    assert 'body.phone.strip().startswith("+")' in source
    assert '"intent":body.intent' in source


def test_whatsapp_intents_are_distinct_and_only_published_plans_are_shareable():
    contracts = (ROOT / "app/contracts.py").read_text()
    source = (ROOT / "app/main.py").read_text()
    for intent in (
        "GENERAL_MESSAGE", "SHARE_ONBOARDING_LINK", "SHARE_PUBLISHED_PLAN",
        "APPOINTMENT_REMINDER", "FOLLOW_UP_REMINDER", "ASSESSMENT_LINK",
        "PROGRESS_UPDATE", "CUSTOM_MESSAGE",
    ):
        assert intent in contracts
    assert 'body.intent == "SHARE_PUBLISHED_PLAN"' in source
    assert 'body.shareable_type != "PUBLISHED_DIET_PLAN"' in source


def test_onboarding_notification_and_timeline_are_idempotent():
    migration = (ROOT / "alembic/versions/0003_phase1_operating_system.py").read_text()
    source = (ROOT / "app/main.py").read_text()
    assert "uq_practice_onboarding_complete_notification" in migration
    assert "ON CONFLICT (tenant_id,event_type,client_id)" in source
    assert '"actions":["VIEW_CLIENT","WHATSAPP"]' in source
    assert "practice_timeline_events" in source
