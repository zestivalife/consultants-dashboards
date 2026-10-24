from datetime import datetime, timezone

from app.measurement_context import assessment_measurement_sources, resolve_latest_measurements


def row(identifier, kind, value, unit, when, source="CLIENT_REPORTED", *, series=None, version=1, status="VALID"):
    return {
        "id": identifier, "series_id": series or identifier, "measurement_type": kind,
        "value": value, "unit": unit, "measured_at": when, "created_at": when,
        "source": source, "version": version, "status": status,
    }


def test_resolves_each_metric_by_clinical_time_and_not_insertion_order():
    result = resolve_latest_measurements([
        row("w-new", "WEIGHT_KG", 81, "kg", "2026-10-24T08:00:00+00:00"),
        row("h-old", "HEIGHT_CM", 167, "cm", "2026-10-20T08:00:00+00:00", "PROFESSIONALLY_RECORDED"),
        row("w-old", "WEIGHT_KG", 82, "kg", "2026-10-21T08:00:00+00:00", "PROFESSIONALLY_RECORDED"),
    ])
    assert result["latest"]["WEIGHT_KG"]["id"] == "w-new"
    assert result["latest"]["HEIGHT_CM"]["id"] == "h-old"
    assert result["calculations"]["bmi"]["value"] == 29.0
    assert result["calculations"]["weight_change"]["value"] == -1.0


def test_newer_client_report_wins_over_older_professional_observation():
    result = resolve_latest_measurements([
        row("professional", "WEIGHT_KG", 82, "kg", "2026-10-20T08:00:00+00:00", "PROFESSIONALLY_RECORDED"),
        row("client", "WEIGHT_KG", 81, "kg", "2026-10-24T08:00:00+00:00", "CLIENT_REPORTED"),
    ])
    assert result["latest"]["WEIGHT_KG"]["id"] == "client"


def test_latest_correction_replaces_prior_series_version_but_history_is_not_mutated():
    original = row("original", "WEIGHT_KG", 83, "kg", "2026-10-20T08:00:00+00:00", series="series", version=1)
    correction = row("correction", "WEIGHT_KG", 82, "kg", "2026-10-20T08:00:00+00:00", "PROFESSIONALLY_RECORDED", series="series", version=2)
    result = resolve_latest_measurements([original, correction])
    assert result["latest"]["WEIGHT_KG"]["id"] == "correction"
    assert original["value"] == 83


def test_invalid_latest_does_not_replace_older_valid_observation():
    result = resolve_latest_measurements([
        row("valid", "WEIGHT_KG", 82, "kg", "2026-10-20T08:00:00+00:00"),
        row("invalid", "WEIGHT_KG", 900, "kg", "2026-10-24T08:00:00+00:00"),
    ])
    assert result["latest"]["WEIGHT_KG"]["id"] == "valid"
    assert result["rejected"][0]["measurement_id"] == "invalid"


def test_invalid_latest_correction_falls_back_to_prior_valid_series_version():
    result = resolve_latest_measurements([
        row("original", "WEIGHT_KG", 82, "kg", "2026-10-20T08:00:00+00:00", series="weight-series", version=1),
        row("bad-correction", "WEIGHT_KG", 900, "kg", "2026-10-24T08:00:00+00:00", series="weight-series", version=2),
    ])
    assert result["latest"]["WEIGHT_KG"]["id"] == "original"
    assert result["rejected"][0]["measurement_id"] == "bad-correction"


def test_invalid_and_ambiguous_units_are_excluded():
    result = resolve_latest_measurements([
        row("waist-inches", "WAIST_CM", 36, "in", "2026-10-24T08:00:00+00:00"),
    ])
    assert "WAIST_CM" not in result["eligible_latest"]
    assert result["rejected"]


def test_legacy_profile_fallback_is_visible_but_requires_confirmation():
    result = resolve_latest_measurements([], {"height_cm": 167, "weight_kg": 82, "recorded_at": "2026-10-20T08:00:00Z"})
    assert result["latest"]["WEIGHT_KG"]["source"] == "LEGACY_SELF_REPORTED"
    assert result["latest"]["WEIGHT_KG"]["historical_observation"] is False
    assert result["eligible_latest"] == {}
    assert result["requires_professional_confirmation"] is True
    assert result["calculations"]["bmi"]["value"] is None


def test_assessment_sources_preserve_individual_measurement_provenance():
    result = resolve_latest_measurements([
        row("height", "HEIGHT_CM", 167, "cm", "2026-10-20T08:00:00+00:00"),
        row("weight", "WEIGHT_KG", 82, "kg", "2026-10-24T08:00:00+00:00", "PROFESSIONALLY_RECORDED"),
    ])
    sources = assessment_measurement_sources(result)
    assert {item["source_id"] for item in sources} == {"height", "weight"}
    assert all(item["provenance"]["resolver_version"] == "external-measurement-resolver.v1" for item in sources)
    assert next(item for item in sources if item["source_id"] == "weight")["provenance"]["resolved_value"] == 82.0


def test_measurement_context_fingerprint_changes_deterministically():
    first = resolve_latest_measurements([row("weight-a", "WEIGHT_KG", 82, "kg", datetime(2026, 10, 20, tzinfo=timezone.utc))])
    same = resolve_latest_measurements([row("weight-a", "WEIGHT_KG", 82, "kg", datetime(2026, 10, 20, tzinfo=timezone.utc))])
    changed = resolve_latest_measurements([row("weight-b", "WEIGHT_KG", 81, "kg", datetime(2026, 10, 24, tzinfo=timezone.utc))])
    assert first["fingerprint"] == same["fingerprint"]
    assert first["fingerprint"] != changed["fingerprint"]


def test_main_wires_measurements_to_assessment_and_immutable_plan_snapshots():
    source = open("app/main.py", encoding="utf-8").read()
    assert 'clients/{client_id}/diet-plan-context' in source
    assert "assessment_measurement_sources(measurement_context)" in source
    assert "MEASUREMENT_CONTEXT_CHANGED" in source
    assert "DIET_PLAN_MEASUREMENT_CONTEXT_STALE" in source
    assert '"measurement_snapshot":measurement["eligible_latest"]' in source
    assert "plan[\"status\"] in {\"APPROVED\",\"PUBLISHED\",\"ARCHIVED\"}" in source
