from datetime import date, datetime, timezone
from pathlib import Path
import pytest

from app.p15 import adherence_summary, homework_transition


def test_adherence_is_explainable_and_uses_truthful_counts():
    rows = [
        {"start_date": date(2026, 10, 15), "due_date": date(2026, 10, 16), "status": "COMPLETED", "completed_at": datetime(2026, 10, 16, tzinfo=timezone.utc)},
        {"start_date": date(2026, 10, 16), "due_date": date(2026, 10, 17), "status": "MISSED", "completed_at": None},
        {"start_date": date(2026, 10, 17), "due_date": None, "status": "IN_PROGRESS", "completed_at": None},
    ]
    result = adherence_summary(rows, today=date(2026, 10, 18), days=7)
    assert result == {"assigned_count": 3, "completed_count": 1, "missed_count": 1,
                      "on_time_completed_count": 1, "completion_rate": 33.33,
                      "on_time_completion_rate": 33.33, "label": "NEEDS_ATTENTION"}


def test_insufficient_data_is_not_a_negative_label():
    result = adherence_summary([], today=date(2026, 10, 18), days=30)
    assert result["completion_rate"] is None
    assert result["label"] == "INSUFFICIENT_DATA"


def test_homework_transitions_are_deterministic_and_terminal():
    assert homework_transition("NOT_STARTED", "IN_PROGRESS") == "IN_PROGRESS"
    assert homework_transition("IN_PROGRESS", "COMPLETED") == "COMPLETED"
    with pytest.raises(ValueError): homework_transition("COMPLETED", "IN_PROGRESS")


def test_migration_is_additive_and_freeze_safe():
    text = (Path(__file__).parents[1] / "alembic/versions/0015_resources_homework_adherence.py").read_text()
    for table in ("external_resource_definitions", "external_resource_versions", "external_resource_assignments",
                  "external_resource_view_events", "external_homework_assignments", "external_homework_checkins",
                  "external_adherence_observations", "external_resource_audit_events"):
        assert f"CREATE TABLE {table}" in text
    assert "ALTER TABLE" not in text
    assert "practice_tasks" not in text


def test_portal_scope_and_false_viewed_guards_are_explicit():
    text = (Path(__file__).parents[1] / "app/main.py").read_text()
    assert "tenant_id=:tenant AND client_id=:client" in text
    assert "explicit_open" in text
    assert "status=CASE WHEN status='ASSIGNED' THEN 'OPENED'" in text
    assert "READ_RESOURCES" in text and "SUBMIT_HOMEWORK_CHECKIN" in text
