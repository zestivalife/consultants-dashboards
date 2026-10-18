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
    assert section([])["status"] == "EMPTY_CONFIRMED"
    assert section([], failed=True)["status"] == "FAILED"
    restricted = section([], restricted=True)
    assert restricted["status"] == "EMPTY_CONFIRMED"
    assert restricted["restricted"] is True


def test_command_centre_is_external_tenant_scoped_and_migration_free():
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
    # The command centre itself remains migration-free. Later additive migrations
    # may exist, but this route must not depend on their marketplace tables.
    assert "external_consultant_public_profiles" not in route
    assert "external_consultant_marketplace_events" not in route
