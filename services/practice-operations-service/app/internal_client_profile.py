"""Validation and deterministic composition for Internal client enrichments."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


MEASUREMENT_FIELDS = {
    "height_cm", "weight_kg", "waist_cm", "hip_cm", "neck_cm",
    "goal_weight_kg", "body_fat_percent",
}
PROFILE_FIELDS = {
    "goals", "dob_display_format", "measurements", "medical_history_narrative",
    "sleep_stress_narrative", "health_record_dates",
}


def _number(value: Any, *, minimum: float, maximum: float) -> float | None:
    if value is None or value == "":
        return None
    number = float(value)
    if number < minimum or number > maximum:
        raise ValueError(f"Measurement must be between {minimum} and {maximum}")
    return number


def validate_enrichment(values: dict[str, Any]) -> dict[str, Any]:
    unknown = set(values) - PROFILE_FIELDS
    if unknown:
        raise ValueError(f"Unsupported enrichment fields: {', '.join(sorted(unknown))}")
    result: dict[str, Any] = {}
    if "goals" in values:
        goals = values["goals"]
        if not isinstance(goals, list) or len(goals) > 3:
            raise ValueError("A maximum of three health and wellness goals is allowed")
        cleaned = [str(goal).strip() for goal in goals]
        if any(not goal or len(goal) > 120 for goal in cleaned) or len(set(cleaned)) != len(cleaned):
            raise ValueError("Goals must be unique non-empty values of at most 120 characters")
        result["goals"] = cleaned
    if "dob_display_format" in values:
        if values["dob_display_format"] not in (None, "DD/MM/YYYY"):
            raise ValueError("DOB display format must be DD/MM/YYYY")
        result["dob_display_format"] = values["dob_display_format"]
    if "measurements" in values:
        measurements = values["measurements"]
        if not isinstance(measurements, dict) or set(measurements) - (MEASUREMENT_FIELDS | {"recorded_at"}):
            raise ValueError("Unsupported measurement field")
        ranges = {
            "height_cm": (30, 300), "weight_kg": (1, 500), "waist_cm": (10, 400),
            "hip_cm": (10, 400), "neck_cm": (5, 200), "goal_weight_kg": (1, 500),
            "body_fat_percent": (0, 100),
        }
        cleaned_measurements = {key: _number(measurements.get(key), minimum=low, maximum=high)
                                for key, (low, high) in ranges.items() if key in measurements}
        if "recorded_at" in measurements:
            recorded_at = measurements["recorded_at"]
            if recorded_at not in (None, ""):
                datetime.fromisoformat(str(recorded_at).replace("Z", "+00:00"))
            cleaned_measurements["recorded_at"] = recorded_at or None
        if any(cleaned_measurements.get(field) is not None for field in MEASUREMENT_FIELDS) and not cleaned_measurements.get("recorded_at"):
            raise ValueError("Measurement date and time is required when saving measurements")
        result["measurements"] = cleaned_measurements
    for field in ("medical_history_narrative", "sleep_stress_narrative"):
        if field in values:
            value = values[field]
            if value is not None and (not isinstance(value, str) or len(value) > 10000):
                raise ValueError(f"{field} must contain at most 10000 characters")
            result[field] = value.strip() if isinstance(value, str) else None
    if "health_record_dates" in values:
        records = values["health_record_dates"]
        if not isinstance(records, dict) or len(records) > 250:
            raise ValueError("Health record date metadata must be an object of at most 250 records")
        cleaned_records: dict[str, dict[str, str | None]] = {}
        for record_id, metadata in records.items():
            if not record_id or len(str(record_id)) > 160 or not isinstance(metadata, dict):
                raise ValueError("Invalid health record date metadata")
            if set(metadata) - {"report_date", "confirmation_date"}:
                raise ValueError("Unsupported health record date field")
            item = {}
            for field in ("report_date", "confirmation_date"):
                value = metadata.get(field)
                if value not in (None, ""):
                    date.fromisoformat(str(value))
                item[field] = value or None
            cleaned_records[str(record_id)] = item
        result["health_record_dates"] = cleaned_records
    return result


def merge_enrichment(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge allowlisted partial updates without erasing unrelated nested fields."""
    merged = {**existing, **incoming}
    if "measurements" in incoming:
        merged["measurements"] = {**(existing.get("measurements") or {}), **incoming["measurements"]}
    if "health_record_dates" in incoming:
        record_dates = {key: dict(value) for key, value in (existing.get("health_record_dates") or {}).items()}
        for record_id, values in incoming["health_record_dates"].items():
            record_dates[record_id] = {**record_dates.get(record_id, {}), **values}
        merged["health_record_dates"] = record_dates
    return merged


def bmi(height_cm: Any, weight_kg: Any) -> float | None:
    try:
        height, weight = float(height_cm), float(weight_kg)
    except (TypeError, ValueError):
        return None
    return round(weight / ((height / 100) ** 2), 1) if height > 0 and weight > 0 else None


def waist_hip_ratio(waist_cm: Any, hip_cm: Any) -> float | None:
    try:
        waist, hip = float(waist_cm), float(hip_cm)
    except (TypeError, ValueError):
        return None
    return round(waist / hip, 2) if waist > 0 and hip > 0 else None


def projection(values: dict[str, Any], version: int, provenance: dict[str, Any]) -> dict[str, Any]:
    measurements = values.get("measurements") or {}
    return {
        **values,
        "derived": {
            "bmi": bmi(measurements.get("height_cm"), measurements.get("weight_kg")),
            "waist_hip_ratio": waist_hip_ratio(measurements.get("waist_cm"), measurements.get("hip_cm")),
        },
        "version": version,
        "schema_version": 1,
        "provenance": provenance,
    }
