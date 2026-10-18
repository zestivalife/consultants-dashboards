from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts import ClientPackageAssign, PackageSessionUse, ServicePackageCreate

ROOT = Path(__file__).parents[1]


def test_p12_migration_is_additive_external_only():
    source=(ROOT/"alembic/versions/0012_packages_programmes.py").read_text()
    for table in (
        "external_service_packages","external_package_versions","external_client_packages",
        "external_client_package_sessions","external_programme_milestones","external_renewal_events",
    ):
        assert f"CREATE TABLE {table}" in source
    assert "ALTER TABLE" not in source
    assert "ZESTIVA_INTERNAL" not in source


def test_package_contract_validates_price_sessions_and_duration():
    package=ServicePackageCreate(name="Six-session programme",session_allowance=6,duration_days=42,
                                 price_minor=120000,currency="INR")
    assert package.snapshot()["session_allowance"] == 6
    for values in ({"session_allowance":0,"duration_days":42},{"session_allowance":6,"duration_days":0}):
        with pytest.raises(ValidationError):
            ServicePackageCreate(name="Invalid",**values)


def test_assignment_and_session_usage_contracts_are_explicit():
    assignment=ClientPackageAssign(client_id="client-a",package_id="8df2829e-8c09-4c62-b52d-f32f366fc5ed",
        start_date=date(2026,10,1),end_date=date(2026,11,12),status="ACTIVE")
    usage=PackageSessionUse(consultation_id="consultation-a",occurred_at=datetime.now(timezone.utc))
    assert assignment.client_id == "client-a"
    assert usage.consultation_id == "consultation-a"


def test_package_queries_are_tenant_and_client_scoped_and_never_auto_renew():
    source=(ROOT/"app/main.py").read_text()
    section=source[source.index('@app.get("/api/v1/practice-operations/packages")'):]
    assert "tenant_id=:tenant" in section
    assert "client_id=:client" in section
    assert "GREATEST(cp.sessions_total-COUNT(s.id)::int,0)" in section
    assert "PACKAGE_ENDING_SOON" in section and "SESSIONS_LOW" in section
    assert "AUTO_RENEW" not in section


def test_client_portal_package_projection_exposes_no_notes_or_price():
    source=(ROOT/"app/main.py").read_text()
    section=source[source.index('@app.get("/api/v1/client-portal/{token}")'):]
    projection=section[section.index("packages ="):section.index('return {"success": True')]
    assert "cp.notes" not in projection
    assert "price_minor" not in projection
    assert "cp.tenant_id=:tenant AND cp.client_id=:client" in projection
