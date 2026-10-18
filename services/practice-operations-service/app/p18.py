"""P18 privacy-safe Practice Analytics helpers."""
from datetime import datetime, timedelta, timezone

PRESETS = {"7d": 7, "30d": 30, "90d": 90}
MIN_COHORT_SIZE = 5


def analytics_window(preset="30d", start=None, end=None, now=None):
    now = now or datetime.now(timezone.utc)
    if preset == "custom":
        if not start or not end or start >= end:
            raise ValueError("A valid custom date range is required")
        return start, end
    if preset == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now
    if preset == "last_month":
        this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_end = this_month
        previous_start = (this_month - timedelta(days=1)).replace(day=1)
        return previous_start, previous_end
    if preset not in PRESETS:
        raise ValueError("Unsupported analytics date range")
    return now - timedelta(days=PRESETS[preset]), now


def rate(completed, total):
    return None if not total else round((completed / total) * 100, 2)


def cohort_result(count, payload):
    return {"state": "INSUFFICIENT_COHORT", "cohort_size": count, "minimum": MIN_COHORT_SIZE} if count < MIN_COHORT_SIZE else {"state": "AVAILABLE", "cohort_size": count, **payload}

