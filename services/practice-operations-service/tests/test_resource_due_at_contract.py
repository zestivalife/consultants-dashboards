from datetime import datetime, timezone

from app.contracts import ResourceCreate, ResourceUpdate


def test_resource_create_parses_browser_datetime_for_postgres():
    payload = ResourceCreate(
        client_id="client-1",
        type="STANDARD",
        title="Synthetic consultation",
        status="SCHEDULED",
        due_at="2026-10-27T11:00:00Z",
    )

    assert payload.due_at == datetime(2026, 10, 27, 11, 0, tzinfo=timezone.utc)


def test_resource_update_parses_browser_datetime_for_postgres():
    payload = ResourceUpdate(version=1, due_at="2026-10-28T12:30:00+00:00")

    assert payload.due_at == datetime(2026, 10, 28, 12, 30, tzinfo=timezone.utc)
