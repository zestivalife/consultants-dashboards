from datetime import datetime, timezone
from typing import Any

CONSULTATION_TRANSITIONS = {
    "RESCHEDULE": ({"SCHEDULED"}, "SCHEDULED"),
    "START": ({"SCHEDULED"}, "IN_PROGRESS"),
    "COMPLETE": ({"IN_PROGRESS"}, "COMPLETED"),
    "CANCEL": ({"SCHEDULED", "IN_PROGRESS"}, "CANCELLED"),
    "MARK_NO_SHOW": ({"SCHEDULED"}, "NO_SHOW"),
}


def consultation_transition(current: str, action: str) -> str:
    allowed, target = CONSULTATION_TRANSITIONS[action]
    if current not in allowed:
        raise ValueError(f"{action} is not allowed from {current}")
    return target


def calendar_window(view: str, anchor: datetime) -> tuple[datetime, datetime]:
    anchor = anchor.astimezone(timezone.utc)
    day = anchor.replace(hour=0, minute=0, second=0, microsecond=0)
    if view in {"AGENDA", "DAY"}:
        from datetime import timedelta
        return day, day + timedelta(days=1 if view == "DAY" else 30)
    if view == "WEEK":
        from datetime import timedelta
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=7)
    if view == "MONTH":
        if day.month == 12:
            end = day.replace(year=day.year + 1, month=1, day=1)
        else:
            end = day.replace(month=day.month + 1, day=1)
        return day.replace(day=1), end
    raise ValueError("Unsupported calendar view")


def factual_summary(parts: dict[str, Any]) -> dict[str, Any]:
    """Stable projection only: no inferred diagnoses, scores, or recommendations."""
    ordered = (
        "last_consultation", "latest_measurements", "recent_reports",
        "biomarker_changes", "goals", "checkins", "adherence",
        "open_tasks", "latest_diet_plan", "missed_followups",
    )
    return {key: parts.get(key, [] if key.endswith("s") or key in {"goals", "checkins", "adherence"} else None) for key in ordered}
