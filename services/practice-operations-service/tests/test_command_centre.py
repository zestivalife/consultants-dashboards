from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.command_centre import next_action, operational_priority, section, sort_work


def test_operational_priority_is_deterministic_and_non_clinical():
    now = datetime.now(timezone.utc)
    assert operational_priority(now - timedelta(minutes=1)) == "URGENT_OPERATIONAL"
    assert operational_priority(now + timedelta(hours=2)) == "TODAY"
    assert operational_priority(now + timedelta(days=3)) == "UPCOMING"
    assert operational_priority(now + timedelta(days=30)) == "LOW"
    assert operational_priority(signal="INVOICE_OVERDUE") == "URGENT_OPERATIONAL"


def test_next_action_and_sorting_are_traceable():
    assert next_action("CONSENT_PENDING") == {"label": "Request consent", "target": "consents"}
    assert next_action("UNKNOWN") == {"label": "Open client", "target": "client"}
    items = [{"id": "2", "priority": "LOW"}, {"id": "1", "priority": "TODAY"}]
    assert [item["id"] for item in sort_work(items)] == ["1", "2"]


def test_section_states_never_turn_failure_or_restriction_into_false_zero():
    assert section([])["status"] == "CONFIRMED_EMPTY"
    assert section([], failed=True)["status"] == "FAILED"
    assert section([{"id": "1"}], partial=True)["status"] == "PARTIAL"
    assert section([], configuration_required=True)["status"] == "CONFIGURATION_REQUIRED"
    restricted = section([], restricted=True)
    assert restricted["status"] == "CONFIRMED_EMPTY"
    assert restricted["restricted"] is True


def test_command_centre_is_external_tenant_scoped_and_integrates_existing_domains():
    root = Path(__file__).parents[1]
    main = (root / "app/main.py").read_text()
    route = main[main.index('@app.get("/api/v1/practice-operations/dashboard/command-centre")'):]
    route = route.split("\n# P31 Consultant Marketplace", 1)[0]
    assert "external_only(request,ctx)" in route
    assert "tenant_id=:tenant" in route
    assert "external_client_team_assignments" in route
    assert 'overall="PARTIAL_DATA" if failed' in route
    assert 'else "CONFIRMED_EMPTY"' in route
    assert "clinical" not in route.lower()
    assert "external_consultant_public_profiles" in route
    assert "external_consultant_marketplace_enrolments" in route
    assert "external_consultant_dashboard_state" in route
    assert "PRACTITIONER_PRIVATE" in route
    assert "last_seen_at" in route


def test_p32_migration_is_additive_external_only_and_0031_is_unchanged():
    root = Path(__file__).parents[1]
    migration = (root / "alembic/versions/0032_consultant_command_centre.py").read_text()
    assert 'down_revision="0031_consultant_marketplace"' in migration
    assert "CREATE TABLE external_consultant_dashboard_state" in migration
    assert "tenant_id" in migration and "user_id" in migration
    assert "dashboard_last_seen_at" in migration
    assert "ZESTIVA_INTERNAL" not in migration
