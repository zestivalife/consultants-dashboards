from datetime import date
from pathlib import Path

import pytest

from app.external_measurements import calendar_age, calculated_health_parameters, completeness, validated_measurement

ROOT = Path(__file__).parents[1]


def row(value, measured_at="2026-10-24T10:00:00+00:00"):
    return {"value": value, "measured_at": measured_at, "source": "PROFESSIONALLY_RECORDED"}


def test_measurements_validate_units_ranges_and_non_finite_values():
    assert validated_measurement("weight_kg", 72.5, "kg")[0] == "WEIGHT_KG"
    for value in (float("nan"), float("inf"), 0, 501):
        with pytest.raises(ValueError):
            validated_measurement("WEIGHT_KG", value, "kg")
    with pytest.raises(ValueError, match="must use cm"):
        validated_measurement("HEIGHT_CM", 170, "inch")


def test_calendar_age_uses_calendar_dates_and_rejects_future_birth_dates():
    assert calendar_age("2000-10-25", date(2026, 10, 24)) == 25
    assert calendar_age("2000-10-24", date(2026, 10, 24)) == 26
    assert calendar_age("2027-01-01", date(2026, 10, 24)) is None


def test_calculations_are_versioned_and_never_invent_missing_inputs():
    latest = {"HEIGHT_CM": row(170), "WEIGHT_KG": row(68), "WAIST_CM": row(80), "HIP_CM": row(100)}
    calculations = calculated_health_parameters(latest, [row(68), row(70, "2026-09-24T10:00:00+00:00")])
    assert calculations["bmi"] == {"value": 23.5, "unit": "kg/m²", "methodology": "bmi.metric.v1", "status": "AVAILABLE", "missing_input_reason": None}
    assert calculations["waist_to_hip_ratio"]["value"] == .8
    assert calculations["waist_to_height_ratio"]["value"] == .47
    assert calculations["weight_change"]["value"] == -2
    assert calculations["weight_change_percentage"]["value"] == -2.86
    missing = calculated_health_parameters({}, [])
    assert missing["bmi"]["value"] is None
    assert missing["bmi"]["missing_input_reason"] == "HEIGHT_CM_AND_WEIGHT_KG_REQUIRED"


def test_completeness_reports_categories_and_missing_checklist():
    result = completeness({"full_name": "Demo", "email": "demo.invalid"}, {"HEIGHT_CM": row(170)}, [])
    assert result["personal_profile"]["percent"] == 50
    assert result["personal_profile"]["missing_fields"] == ["date_of_birth", "phone"]
    assert result["body_measurements"]["missing_fields"] == ["WEIGHT_KG"]
    assert result["clinical_evidence"]["optional"] is True


def test_measurement_schema_and_routes_are_external_tenant_scoped_and_append_only():
    migrations = (ROOT / "external_migrations/runner.py").read_text()
    source = (ROOT / "app/main.py").read_text()
    assert "external_0055_client_measurements" in migrations
    assert "external_client_measurements" in migrations
    assert "supersedes_id" in migrations and "correction_reason" in migrations
    assert 'clients/{client_id}/measurements' in source
    assert "m.tenant_id=:tenant AND m.client_id=:client" in source
    assert "version=row[\"version\"]+1" not in source  # parameters stay bound, not interpolated
    assert "DELETE FROM external_client_measurements" not in source
    assert "UPDATE external_client_measurements" not in source
