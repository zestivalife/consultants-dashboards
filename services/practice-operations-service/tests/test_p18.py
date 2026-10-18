from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.p18 import MIN_COHORT_SIZE, analytics_window, cohort_result, rate

ROOT=Path(__file__).parents[1]


def test_date_presets_and_completion_rates_are_deterministic():
    now=datetime(2026,10,18,tzinfo=timezone.utc)
    start,end=analytics_window("30d",now=now)
    assert (end-start).days==30
    assert rate(3,4)==75
    assert rate(0,0) is None
    with pytest.raises(ValueError):analytics_window("unknown",now=now)


def test_outcome_cohort_privacy_fails_closed():
    assert cohort_result(MIN_COHORT_SIZE-1,{"observations":99})["state"]=="INSUFFICIENT_COHORT"
    assert cohort_result(MIN_COHORT_SIZE,{"observations":8})["state"]=="AVAILABLE"


def test_p18_migration_is_external_only_and_expand_only():
    source=(ROOT/"alembic/versions/0018_practice_analytics.py").read_text()
    assert 'down_revision = "0017_team_practice_rbac"' in source
    assert "CREATE TABLE external_analytics_snapshots" in source
    assert "CREATE TABLE external_analytics_audit_events" in source
    assert "expand-only" in source
    for frozen in ("external_clients","diet_plan","biomarker","organization_memberships"):
        assert f"ALTER TABLE {frozen}" not in source


def test_p18_endpoint_is_tenant_permission_and_privacy_scoped():
    source=(ROOT/"app/main.py").read_text()
    section=source[source.index('@app.get("/api/v1/practice-operations/analytics/practice")'):source.index("# P19 is referral-scoped")]
    assert '"ANALYTICS_VIEW"' in section
    assert 'tenant_id=:tenant' in section
    assert "PRIVATE_NOTE" not in section
    assert "MIN_COHORT_SIZE" in section
    assert '"UNAVAILABLE_SOURCE"' in section
