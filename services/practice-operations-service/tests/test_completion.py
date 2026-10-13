from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.domain import calendar_window, consultation_transition, factual_summary

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("current,action,target", [
    ("SCHEDULED", "START", "IN_PROGRESS"),
    ("SCHEDULED", "RESCHEDULE", "SCHEDULED"),
    ("IN_PROGRESS", "COMPLETE", "COMPLETED"),
    ("SCHEDULED", "MARK_NO_SHOW", "NO_SHOW"),
])
def test_consultation_lifecycle(current, action, target):
    assert consultation_transition(current, action) == target


def test_consultation_lifecycle_rejects_invalid_transition():
    with pytest.raises(ValueError):
        consultation_transition("COMPLETED", "START")


def test_calendar_windows_are_deterministic():
    anchor = datetime(2026, 10, 13, 16, 45, tzinfo=timezone.utc)
    week_start, week_end = calendar_window("WEEK", anchor)
    assert week_start.isoformat() == "2026-10-12T00:00:00+00:00"
    assert (week_end - week_start).days == 7
    month_start, month_end = calendar_window("MONTH", anchor)
    assert month_start.day == 1
    assert month_end.isoformat() == "2026-11-01T00:00:00+00:00"


def test_summary_is_factual_and_stably_ordered():
    summary = factual_summary({"goals": [{"id": "g1"}], "latest_diet_plan": {"id": "d1"}})
    assert list(summary) == [
        "last_consultation", "latest_measurements", "recent_reports",
        "biomarker_changes", "goals", "checkins", "adherence", "open_tasks",
        "latest_diet_plan", "missed_followups",
    ]
    assert summary["goals"] == [{"id": "g1"}]
    assert "interpretation" not in summary


def test_completion_schema_is_append_only_and_reference_only():
    migration = (ROOT / "alembic/versions/0002_practice_operations_completion.py").read_text()
    assert "practice_goal_progress_entries" in migration
    assert "practice_media_references" in migration
    assert "document_reference" in migration
    assert "BYTEA" not in migration
    assert "service_outbox_deliveries" in migration
    assert "PRIMARY KEY (consumer_name,event_id)" in migration


def test_completion_api_keeps_tenant_and_idempotency_guards():
    source = (ROOT / "app/main.py").read_text()
    for value in (
        "INVALID_CONSULTATION_TRANSITION", "practice_goal_progress_entries",
        "calendar/events", "preconsult-summary", "service_outbox_deliveries",
        "ON CONFLICT (consumer_name,event_id) DO NOTHING",
    ):
        assert value in source
    assert "tenant_id=:tenant_id" in source
