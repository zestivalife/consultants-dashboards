from pathlib import Path

import pytest

from app.external_client_profile import (
    bmi,
    merge_external_enrichment,
    projection,
    validate_external_enrichment,
    waist_hip_ratio,
)

ROOT = Path(__file__).parents[1]


def test_external_measurement_derivations_require_valid_source_values():
    assert bmi(170, 70) == 24.2
    assert bmi(None, 70) is None
    assert bmi(0, 70) is None
    assert waist_hip_ratio(80, 100) == 0.8
    assert waist_hip_ratio(80, 0) is None


def test_external_goals_are_unique_and_limited_to_three():
    assert validate_external_enrichment({"goals": ["Better sleep", "Improve energy", "Improve nutrition"]})["goals"] == [
        "Better sleep", "Improve energy", "Improve nutrition"
    ]
    with pytest.raises(ValueError, match="maximum of three"):
        validate_external_enrichment({"goals": ["a", "b", "c", "d"]})
    with pytest.raises(ValueError, match="unique"):
        validate_external_enrichment({"goals": ["a", "a"]})


def test_external_narratives_dates_and_anthropometrics_accept_normal_input():
    result = validate_external_enrichment({
        "date_of_birth": "1990-04-23",
        "medical_history_narrative": "Family history of hypertension. No prior surgery.",
        "sleep_stress_narrative": "Sleeps 7 hours. Moderate work stress.",
        "measurements": {
            "height_cm": 200,
            "weight_kg": 100,
            "waist_cm": 80,
            "hip_cm": 100,
            "neck_cm": 36,
            "recorded_at": "2026-10-22T10:00:00+00:00",
        },
        "health_record_dates": {"record-1": {"report_date": "2026-10-01", "confirmation_date": "2026-10-02"}},
    })
    projected = projection(result, 2, {"source": "EXTERNAL_CLIENT360"})
    assert projected["derived"] == {"bmi": 25.0, "waist_hip_ratio": 0.8}
    assert projected["medical_history_narrative"].startswith("Family history")
    assert projected["health_record_dates"]["record-1"]["confirmation_date"] == "2026-10-02"


def test_external_partial_merge_preserves_other_client_fields():
    merged = merge_external_enrichment(
        {"measurements": {"height_cm": 170, "weight_kg": 70}, "goals": ["A"]},
        {"measurements": {"weight_kg": 71, "recorded_at": "2026-10-22T10:00:00Z"}},
    )
    assert merged["measurements"]["height_cm"] == 170
    assert merged["measurements"]["weight_kg"] == 71
    assert merged["goals"] == ["A"]


def test_external_only_additive_migration_and_api_are_tenant_client_scoped():
    migration = (ROOT / "alembic/versions/0053_external_client_profile_enrichments.py").read_text()
    source = (ROOT / "app/main.py").read_text()
    assert 'down_revision = "0052_internal_profile"' in migration
    assert "external_client_profile_enrichments" in migration
    assert "PRIMARY KEY (tenant_id, client_id)" in migration
    assert "audit_history JSONB" in migration
    assert 'clients/{client_id}/profile-enrichment' in source
    assert "denied=external_only(request,ctx)" in source
    assert "WHERE tenant_id=:tenant AND client_id=:client" in source
    assert "audit_history=audit_history ||" in source
    assert "merged_values=merge_external_enrichment" in source


def test_diet_plan_create_persists_all_selected_health_goals():
    contracts = (ROOT / "app/contracts.py").read_text()
    source = (ROOT / "app/main.py").read_text()
    assert "health_goals: list[str]" in contracts
    assert "max_length=3" in contracts
    assert '"health_goals":body.health_goals' in source
