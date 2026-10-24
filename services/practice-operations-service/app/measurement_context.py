"""Canonical, external-only measurement resolution for nutrition workflows."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from app.external_measurements import calculated_health_parameters, validated_measurement


TYPE_TO_PROFILE_FIELD = {
    "HEIGHT_CM": "height_cm",
    "WEIGHT_KG": "weight_kg",
    "WAIST_CM": "waist_cm",
    "HIP_CM": "hip_cm",
    "NECK_CM": "neck_cm",
    "CHEST_CM": "chest_cm",
    "MID_UPPER_ARM_CM": "mid_upper_arm_cm",
    "THIGH_CM": "thigh_cm",
    "CALF_CM": "calf_cm",
}
PROFILE_FIELD_TO_TYPE = {value: key for key, value in TYPE_TO_PROFILE_FIELD.items()}
SOURCE_PRIORITY = {"PROFESSIONALLY_RECORDED": 3, "DOCUMENT_DERIVED": 2, "CLIENT_REPORTED": 1}


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _eligible(row: dict[str, Any]) -> tuple[bool, str | None]:
    if str(row.get("status") or "VALID").upper() in {"INVALID", "INVALIDATED", "QUARANTINED"}:
        return False, "INVALIDATED_OBSERVATION"
    try:
        validated_measurement(row.get("measurement_type"), row.get("value"), row.get("unit"))
    except ValueError as exc:
        return False, str(exc)
    return True, None


def resolve_latest_measurements(rows: list[dict[str, Any]], legacy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve each metric independently by clinical time, correction version and provenance.

    Longitudinal observations always outrank the legacy profile. Source priority is only a
    deterministic tie-breaker for observations recorded at the same clinical time; a newer
    client-reported observation therefore is not displaced by an older professional value.
    """
    series_rows: dict[str, list[dict[str, Any]]] = {}
    rejected: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        key = str(row.get("series_id") or row.get("id"))
        series_rows.setdefault(key, []).append(row)

    eligible: list[dict[str, Any]] = []
    for versions in series_rows.values():
        versions.sort(key=lambda row: int(row.get("version") or 0), reverse=True)
        for row in versions:
            valid, reason = _eligible(row)
            if valid:
                eligible.append(row)
                break
            rejected.append({"measurement_id": str(row.get("id") or ""), "measurement_type": row.get("measurement_type"), "reason": reason})
    eligible.sort(key=lambda row: (
        _timestamp(row.get("measured_at")),
        int(row.get("version") or 0),
        SOURCE_PRIORITY.get(str(row.get("source") or ""), 0),
        str(row.get("id") or ""),
    ), reverse=True)

    latest: dict[str, dict[str, Any]] = {}
    for row in eligible:
        kind = str(row["measurement_type"])
        if kind not in latest:
            latest[kind] = {
                **row,
                "id": str(row.get("id") or ""),
                "series_id": str(row.get("series_id") or row.get("id") or ""),
                "value": float(row["value"]),
                "validity_status": "VALID",
                "eligibility": "ELIGIBLE",
            }

    legacy = dict(legacy or {})
    legacy_observed = legacy.get("recorded_at")
    for field, kind in PROFILE_FIELD_TO_TYPE.items():
        if kind in latest or legacy.get(field) in (None, ""):
            continue
        unit = "kg" if kind == "WEIGHT_KG" else "cm"
        try:
            _, value, canonical_unit = validated_measurement(kind, legacy[field], unit)
            observed = _timestamp(legacy_observed)
            status = "NEEDS_CONFIRMATION"
            latest[kind] = {
                "id": f"legacy-profile:{kind.lower()}",
                "series_id": None,
                "measurement_type": kind,
                "value": float(value),
                "unit": canonical_unit,
                "measured_at": observed.isoformat() if legacy_observed else None,
                "source": "LEGACY_SELF_REPORTED",
                "version": 1,
                "validity_status": status,
                "eligibility": "REVIEW_REQUIRED",
                "historical_observation": False,
            }
        except ValueError as exc:
            rejected.append({"measurement_id": f"legacy-profile:{kind.lower()}", "measurement_type": kind, "reason": str(exc)})

    governed = {kind: row for kind, row in latest.items() if row.get("eligibility") == "ELIGIBLE"}
    weights = [row for row in eligible if row.get("measurement_type") == "WEIGHT_KG"]
    calculations = calculated_health_parameters(governed, weights)
    source_ids = sorted(str(row["id"]) for row in governed.values())
    fingerprint = sha256(json.dumps({
        "sources": [{"id": row["id"], "version": row.get("version"), "measured_at": str(row.get("measured_at")), "value": row["value"], "unit": row["unit"]} for row in governed.values()],
        "calculations": calculations,
    }, sort_keys=True, default=str).encode()).hexdigest()
    return {
        "latest": latest,
        "eligible_latest": governed,
        "calculations": calculations,
        "rejected": rejected,
        "source_measurement_ids": source_ids,
        "fingerprint": fingerprint,
        "requires_professional_confirmation": any(row.get("eligibility") == "REVIEW_REQUIRED" for row in latest.values()),
        "resolver_version": "external-measurement-resolver.v1",
    }


def assessment_measurement_sources(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Build traceable assessment sources without inventing combined observation records."""
    sources = []
    for kind, row in sorted((context.get("eligible_latest") or {}).items()):
        field = TYPE_TO_PROFILE_FIELD[kind]
        sources.append({
            "source_type": "MEASUREMENT",
            "source_id": str(row["id"]),
            "source_version": str(row.get("version") or 1),
            "status": "AVAILABLE",
            "observed_at": row.get("measured_at"),
            "data": {field: row["value"], "unit": row["unit"], "measurement_type": kind},
            "provenance": {
                "source": row.get("source"),
                "series_id": row.get("series_id"),
                "resolver_version": context["resolver_version"],
                "resolved_value": row["value"],
                "resolved_unit": row["unit"],
            },
        })
    return sources
