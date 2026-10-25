from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts import AppointmentTypeCreate, AvailabilityRuleCreate, WaitlistCreate

ROOT=Path(__file__).parents[1]


def test_p13_migration_is_additive_external_only():
    source=(ROOT/"alembic/versions/0013_scheduling.py").read_text()
    for table in ("external_appointment_types","external_availability_rules","external_booking_links",
                  "external_scheduled_appointments","external_scheduling_waitlist","external_scheduling_audit_events"):
        assert f"CREATE TABLE {table}" in source
    assert "ALTER TABLE" not in source
    assert "practice_consultations" not in source
    assert "ZESTIVA_INTERNAL" not in source


def test_scheduling_contracts_enforce_safe_windows_and_durations():
    kind=AppointmentTypeCreate(name="Review",duration_minutes=45,location_type="ONLINE")
    rule=AvailabilityRuleCreate(weekday=1,start_time="09:00",end_time="17:00",timezone="Asia/Kolkata")
    waitlist=WaitlistCreate(client_id="client-a",appointment_type_id="8df2829e-8c09-4c62-b52d-f32f366fc5ed")
    assert kind.duration_minutes == 45 and rule.weekday == 1 and waitlist.client_id == "client-a"
    assert rule.start_time.isoformat() == "09:00:00" and rule.end_time.isoformat() == "17:00:00"
    with pytest.raises(ValidationError):
        AppointmentTypeCreate(name="Invalid",duration_minutes=1,location_type="ONLINE")
    with pytest.raises(ValidationError):
        AvailabilityRuleCreate(weekday=7,start_time="09:00",end_time="17:00",timezone="UTC")


def test_scheduling_routes_are_tenant_scoped_conflict_safe_and_audited():
    source=(ROOT/"app/main.py").read_text()
    section=source[source.index('@app.get("/api/v1/practice-operations/scheduling/appointment-types")'):]
    assert "tenant_id=:tenant" in section
    assert "APPOINTMENT_SLOT_UNAVAILABLE" in section
    assert "external_scheduling_audit_events" in section
    assert "token_hash=:hash" in section
    assert "attendance_status" in section and 'body.status=="NO_SHOW"' in section
    assert "UPDATE practice_consultations" not in section
    availability=section[section.index('@app.post("/api/v1/practice-operations/scheduling/availability"'):section.index('@app.delete("/api/v1/practice-operations/scheduling/availability')]
    assert "await db.commit()" in availability


def test_calendar_projection_is_additive_and_waitlist_never_auto_books():
    source=(ROOT/"app/main.py").read_text()
    calendar=source[source.index('@app.get("/api/v1/practice-operations/calendar/events")'):source.index('@app.get("/api/v1/practice-operations/clients/{client_id}/preconsult-summary")')]
    assert "external_scheduled_appointments" in calendar
    scheduling=source[source.index('@app.post("/api/v1/practice-operations/scheduling/waitlist"'):]
    assert "'WAITING'" in scheduling
    assert "AUTO_BOOK" not in scheduling
