"""External Client360 longitudinal measurement validation and projections."""
from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import Any

MEASUREMENT_RANGES = {
    "HEIGHT_CM": (30.0, 300.0, "cm"),
    "WEIGHT_KG": (1.0, 500.0, "kg"),
    "WAIST_CM": (10.0, 400.0, "cm"),
    "HIP_CM": (10.0, 400.0, "cm"),
    "NECK_CM": (5.0, 200.0, "cm"),
    "CHEST_CM": (10.0, 400.0, "cm"),
    "MID_UPPER_ARM_CM": (5.0, 200.0, "cm"),
    "THIGH_CM": (5.0, 250.0, "cm"),
    "CALF_CM": (5.0, 200.0, "cm"),
}


def validated_measurement(measurement_type: str, value: Any, unit: str) -> tuple[str, Decimal, str]:
    kind = str(measurement_type).upper()
    if kind not in MEASUREMENT_RANGES:
        raise ValueError("Unsupported measurement type")
    low, high, expected_unit = MEASUREMENT_RANGES[kind]
    if unit != expected_unit:
        raise ValueError(f"{kind} must use {expected_unit}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Measurement value must be numeric") from exc
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{kind} must be between {low:g} and {high:g} {expected_unit}")
    return kind, Decimal(str(number)), expected_unit


def calendar_age(date_of_birth: date | str | None, today: date | None = None) -> int | None:
    if not date_of_birth:
        return None
    born = date.fromisoformat(str(date_of_birth)[:10])
    current = today or date.today()
    if born > current:
        return None
    return current.year - born.year - ((current.month, current.day) < (born.month, born.day))


def _number(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    try:
        value = float(row["value"])
    except (KeyError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value > 0 else None


def calculated_health_parameters(latest: dict[str, dict[str, Any]], weight_history: list[dict[str, Any]]) -> dict[str, Any]:
    height = _number(latest.get("HEIGHT_CM"))
    weight = _number(latest.get("WEIGHT_KG"))
    waist = _number(latest.get("WAIST_CM"))
    hip = _number(latest.get("HIP_CM"))
    comparable_weights = [_number(row) for row in weight_history]
    comparable_weights = [value for value in comparable_weights if value is not None]
    previous = comparable_weights[1] if len(comparable_weights) > 1 else None

    def metric(value, unit, methodology, missing):
        return {"value": value, "unit": unit, "methodology": methodology,
                "status": "AVAILABLE" if value is not None else "MISSING_INPUT",
                "missing_input_reason": None if value is not None else missing}

    bmi = round(weight / ((height / 100) ** 2), 1) if height and weight else None
    whr = round(waist / hip, 2) if waist and hip else None
    whtr = round(waist / height, 2) if waist and height else None
    change = round(weight - previous, 2) if weight and previous else None
    percentage = round(((weight - previous) / previous) * 100, 2) if weight and previous else None
    return {
        "bmi": metric(bmi, "kg/m²", "bmi.metric.v1", "HEIGHT_CM_AND_WEIGHT_KG_REQUIRED"),
        "waist_to_hip_ratio": metric(whr, "ratio", "whr.metric.v1", "WAIST_CM_AND_HIP_CM_REQUIRED"),
        "waist_to_height_ratio": metric(whtr, "ratio", "whtr.metric.v1", "WAIST_CM_AND_HEIGHT_CM_REQUIRED"),
        "weight_change": metric(change, "kg", "weight-change.metric.v1", "TWO_DATED_WEIGHT_RECORDS_REQUIRED"),
        "weight_change_percentage": metric(percentage, "%", "weight-change-percent.metric.v1", "TWO_DATED_WEIGHT_RECORDS_REQUIRED"),
        "weight_trend": {
            "status": "AVAILABLE" if comparable_weights else "MISSING_INPUT",
            "methodology": "weight-trend.dated-observations.v1",
            "observations": weight_history,
            "missing_input_reason": None if comparable_weights else "DATED_WEIGHT_RECORD_REQUIRED",
        },
    }


def completeness(profile: dict[str, Any], latest: dict[str, dict[str, Any]], biomarkers: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {
        "personal_profile": {
            "required": ["full_name", "date_of_birth", "phone", "email"],
            "present": {key for key in ("full_name", "date_of_birth", "phone", "email") if profile.get(key)},
        },
        "medical_background": {
            "required": ["medical_history"],
            "present": {"medical_history"} if profile.get("medical_history") else set(),
        },
        "body_measurements": {
            "required": ["HEIGHT_CM", "WEIGHT_KG"],
            "present": set(latest),
        },
        "lifestyle": {
            "required": ["lifestyle"],
            "present": {"lifestyle"} if profile.get("lifestyle") else set(),
        },
        "clinical_evidence": {
            "required": [],
            "present": {"confirmed_biomarker"} if biomarkers else set(),
        },
    }
    result = {}
    for name, category in categories.items():
        missing = [field for field in category["required"] if field not in category["present"]]
        total = len(category["required"])
        result[name] = {"percent": round(((total - len(missing)) / total) * 100) if total else None,
                        "missing_fields": missing, "optional": total == 0}
    return result
