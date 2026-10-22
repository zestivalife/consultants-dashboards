"""Validation and deterministic projections for External Client360 enrichments."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


PROFILE_FIELDS = {
    "goals", "date_of_birth", "measurements", "medical_history_narrative",
    "sleep_stress_narrative", "health_record_dates",
}
MEASUREMENT_RANGES = {
    "height_cm": (30, 300), "weight_kg": (1, 500), "waist_cm": (10, 400),
    "hip_cm": (10, 400), "neck_cm": (5, 200), "goal_weight_kg": (1, 500),
    "body_fat_percent": (0, 100), "chest_cm": (10, 400),
    "mid_upper_arm_cm": (5, 200), "thigh_cm": (5, 250), "calf_cm": (5, 200),
}


def _number(value: Any, minimum: float, maximum: float) -> float | None:
    if value in (None, ""):
        return None
    number = float(value)
    if number < minimum or number > maximum:
        raise ValueError(f"Measurement must be between {minimum} and {maximum}")
    return number


def validate_external_enrichment(values: dict[str, Any]) -> dict[str, Any]:
    unknown = set(values) - PROFILE_FIELDS
    if unknown:
        raise ValueError(f"Unsupported External profile fields: {', '.join(sorted(unknown))}")
    result: dict[str, Any] = {}
    if "goals" in values:
        goals = values["goals"]
        if not isinstance(goals, list) or not 0 <= len(goals) <= 3:
            raise ValueError("A maximum of three health and wellness goals is allowed")
        cleaned = [str(goal).strip() for goal in goals]
        if any(not goal or len(goal) > 120 for goal in cleaned) or len(set(cleaned)) != len(cleaned):
            raise ValueError("Goals must be unique non-empty values of at most 120 characters")
        result["goals"] = cleaned
    if "date_of_birth" in values:
        value = values["date_of_birth"]
        if value not in (None, ""):
            date.fromisoformat(str(value))
        result["date_of_birth"] = value or None
    if "measurements" in values:
        measurements = values["measurements"]
        if not isinstance(measurements, dict) or set(measurements) - (set(MEASUREMENT_RANGES) | {"recorded_at"}):
            raise ValueError("Unsupported External measurement field")
        cleaned = {
            key: _number(measurements.get(key), low, high)
            for key, (low, high) in MEASUREMENT_RANGES.items() if key in measurements
        }
        if "recorded_at" in measurements:
            recorded_at = measurements["recorded_at"]
            if recorded_at not in (None, ""):
                datetime.fromisoformat(str(recorded_at).replace("Z", "+00:00"))
            cleaned["recorded_at"] = recorded_at or None
        if any(cleaned.get(field) is not None for field in MEASUREMENT_RANGES) and not cleaned.get("recorded_at"):
            raise ValueError("Measurement date and time is required when saving measurements")
        result["measurements"] = cleaned
    for field in ("medical_history_narrative", "sleep_stress_narrative"):
        if field in values:
            value = values[field]
            if value is not None and (not isinstance(value, str) or len(value) > 10000):
                raise ValueError(f"{field} must contain at most 10000 characters")
            result[field] = value.strip() if isinstance(value, str) else None
    if "health_record_dates" in values:
        records = values["health_record_dates"]
        if not isinstance(records, dict) or len(records) > 250:
            raise ValueError("Health record dates must be an object of at most 250 records")
        cleaned_records = {}
        for record_id, metadata in records.items():
            if not record_id or len(str(record_id)) > 160 or not isinstance(metadata, dict):
                raise ValueError("Invalid Health Record date metadata")
            if set(metadata) - {"report_date", "confirmation_date"}:
                raise ValueError("Unsupported Health Record date field")
            item = {}
            for field in ("report_date", "confirmation_date"):
                value = metadata.get(field)
                if value not in (None, ""):
                    date.fromisoformat(str(value))
                item[field] = value or None
            cleaned_records[str(record_id)] = item
        result["health_record_dates"] = cleaned_records
    return result


def merge_external_enrichment(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing, **incoming}
    for field in ("measurements", "health_record_dates"):
        if field in incoming:
            merged[field] = {**(existing.get(field) or {}), **incoming[field]}
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
