from datetime import date, timedelta

TERMINAL = {"COMPLETED", "MISSED", "CANCELLED"}


def adherence_summary(rows, *, today: date, days: int):
    start = today - timedelta(days=days - 1)
    eligible = [row for row in rows if start <= row["start_date"] <= today]
    assigned = len(eligible)
    completed = sum(row["status"] == "COMPLETED" for row in eligible)
    missed = sum(row["status"] == "MISSED" for row in eligible)
    on_time = sum(row["status"] == "COMPLETED" and row.get("completed_at") and
                  (not row.get("due_date") or row["completed_at"].date() <= row["due_date"]) for row in eligible)
    rate = round(completed * 100 / assigned, 2) if assigned else None
    on_time_rate = round(on_time * 100 / assigned, 2) if assigned else None
    label = "INSUFFICIENT_DATA" if assigned < 2 else "GOOD" if rate >= 80 else "MODERATE" if rate >= 50 else "NEEDS_ATTENTION"
    return {"assigned_count": assigned, "completed_count": completed, "missed_count": missed,
            "on_time_completed_count": on_time, "completion_rate": rate,
            "on_time_completion_rate": on_time_rate, "label": label}


def homework_transition(current: str, target: str):
    allowed = {
        "NOT_STARTED": {"IN_PROGRESS", "COMPLETED", "MISSED", "CANCELLED"},
        "IN_PROGRESS": {"COMPLETED", "MISSED", "CANCELLED"},
        "COMPLETED": set(), "MISSED": set(), "CANCELLED": set(),
    }
    if target not in allowed.get(current, set()):
        raise ValueError("Homework status transition is not permitted")
    return target
