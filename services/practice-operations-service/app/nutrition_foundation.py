"""External-only nutrition assessment validation and deterministic calculations."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


CALCULATION_VERSIONS = {
    "bmi": "bmi.metric.v1",
    "waist_hip_ratio": "whr.metric.v1",
    "weight_change": "weight-change.metric.v1",
}
SIMULATED_PROVENANCE = {"SIMULATED", "RANDOM", "MOCK", "SYNTHETIC_CLINICAL_VALUE"}
SOURCE_TYPES = {
    "CLIENT_INTAKE", "GOALS", "DIETARY_PREFERENCES", "ALLERGIES",
    "MEDICAL_HISTORY", "MEDICATIONS", "LIFESTYLE", "MEASUREMENT",
    "BIOMARKER", "CONSENT", "CLINICAL_DOCUMENT",
}


class AssessmentSource(BaseModel):
    source_type: str = Field(min_length=1, max_length=60)
    source_id: str = Field(min_length=1, max_length=160)
    source_version: str = Field(min_length=1, max_length=120)
    status: str = Field(default="AVAILABLE", max_length=40)
    observed_at: datetime | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def clinical_safety(self):
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(f"Unsupported assessment source type: {self.source_type}")
        provenance_type = str(self.provenance.get("type") or self.provenance.get("source") or "").upper()
        if provenance_type in SIMULATED_PROVENANCE or self.data.get("simulated") is True:
            raise ValueError("Simulated clinical values are not permitted")
        if self.source_type == "BIOMARKER":
            if self.status != "CONFIRMED":
                raise ValueError("Only confirmed biomarkers may enter a nutrition assessment")
            if not self.data.get("canonical_biomarker_id") or self.data.get("value") is None:
                raise ValueError("Biomarker identity and value are required")
            if not self.data.get("unit") or not self.data.get("source_report_reference"):
                raise ValueError("Biomarker unit and source report reference are required")
        return self


class NutritionConsideration(BaseModel):
    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Z0-9_]+$")
    summary: str = Field(min_length=1, max_length=500)
    source_observation_ids: list[str] = Field(min_length=1, max_length=100)
    professional_review_required: bool = True


class NutritionAssessmentCreate(BaseModel):
    assessment_id: UUID | None = None
    consent_state: Literal["CONFIRMED", "NOT_REQUIRED"]
    sources: list[AssessmentSource] = Field(min_length=1, max_length=500)
    professional_review_state: Literal["NOT_REVIEWED"] = "NOT_REVIEWED"
    clinical_safety_findings: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    nutrition_considerations: list[NutritionConsideration] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def considerations_are_traceable(self):
        source_ids = {source.source_id for source in self.sources}
        for consideration in self.nutrition_considerations:
            unknown = set(consideration.source_observation_ids) - source_ids
            if unknown:
                raise ValueError("Nutrition considerations must reference assessment source observations")
        return self


class NutritionProfile(BaseModel):
    dietary_preference: Literal["VEGETARIAN", "EGG", "NON_VEGETARIAN", "VEGAN"] | None = None
    allergies_intolerances: list[str] = Field(default_factory=list, max_length=100)
    food_restrictions: list[str] = Field(default_factory=list, max_length=100)
    meal_timing_frequency: str | None = Field(default=None, max_length=4000)
    typical_dietary_intake: str | None = Field(default=None, max_length=8000)
    appetite_eating_patterns: str | list[str] | None = None
    water_intake: str | None = Field(default=None, max_length=1000)
    food_dislikes_preferences: str | list[str] | None = None
    nutrition_medical_conditions: list[str] = Field(default_factory=list, max_length=100)
    relevant_medications: list[str] = Field(default_factory=list, max_length=100)
    relevant_supplements: list[str] = Field(default_factory=list, max_length=100)
    weight_management_goals: list[str] = Field(default_factory=list, max_length=50)
    recovery_disease_management_goals: list[str] = Field(default_factory=list, max_length=50)
    consultant_notes: str | None = Field(default=None, max_length=8000)


class NutritionAssessmentSave(BaseModel):
    expected_version: int = Field(ge=0)
    action: Literal["SAVE_DRAFT", "SUBMIT"]
    profile: NutritionProfile
    sources: list[AssessmentSource] = Field(default_factory=list, max_length=500)
    clinical_safety_findings: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


class NutritionAssessmentTransition(BaseModel):
    action: Literal["START_REVIEW", "MARK_REVIEWED", "REQUEST_CHANGES"]
    expected_version: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=4000)


class AssessmentReview(BaseModel):
    decision: Literal["START_REVIEW", "APPROVE", "REQUEST_CHANGES"]
    expected_version: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=4000)


class AssessmentStale(BaseModel):
    source_type: str = Field(min_length=1, max_length=60)
    source_id: str = Field(min_length=1, max_length=160)
    source_version: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=1000)


class DietPlanAssessmentBind(BaseModel):
    assessment_id: UUID
    assessment_version: int = Field(ge=1)
    external_plan_id: str = Field(min_length=1, max_length=160)
    external_plan_version: str = Field(min_length=1, max_length=120)
    plan_state: Literal["DRAFT", "SAVED", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "PUBLISHED"]


class ClinicalDocumentLink(BaseModel):
    document_reference: str = Field(min_length=1, max_length=240)
    health_record_reference: str | None = Field(default=None, max_length=240)
    extraction_run_reference: str | None = Field(default=None, max_length=240)
    observation_references: list[str] = Field(default_factory=list, max_length=500)
    source_available: bool
    source_status: Literal["AVAILABLE", "HISTORICAL_SOURCE_UNAVAILABLE", "QUARANTINED"]

    @model_validator(mode="after")
    def source_truth(self):
        if self.source_available != (self.source_status == "AVAILABLE"):
            raise ValueError("Source availability and status contradict each other")
        return self


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise ValueError("Measurement must be numeric") from exc


def _rounded(value: Decimal, places: str) -> float:
    return float(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def measurement_calculations(sources: list[AssessmentSource]) -> dict[str, Any]:
    measurements = [source for source in sources if source.source_type == "MEASUREMENT"]
    measurements.sort(key=lambda source: source.observed_at or datetime.min, reverse=True)
    latest = measurements[0] if measurements else None
    data = latest.data if latest else {}
    height, weight = _decimal(data.get("height_cm")), _decimal(data.get("weight_kg"))
    waist, hip = _decimal(data.get("waist_cm")), _decimal(data.get("hip_cm"))
    bmi = None
    if height is not None and weight is not None:
        if not Decimal("30") <= height <= Decimal("300") or not Decimal("1") <= weight <= Decimal("500"):
            raise ValueError("Height or weight is outside the supported range")
        bmi = _rounded(weight / ((height / Decimal("100")) ** 2), "0.1")
    whr = None
    if waist is not None and hip is not None:
        if waist <= 0 or hip <= 0:
            raise ValueError("Waist and hip must be positive")
        whr = _rounded(waist / hip, "0.01")
    weight_rows = [(source.observed_at, _decimal(source.data.get("weight_kg"))) for source in measurements]
    weight_rows = [(date, value) for date, value in weight_rows if date is not None and value is not None]
    change = _rounded(weight_rows[0][1] - weight_rows[1][1], "0.1") if len(weight_rows) > 1 else None
    return {
        "bmi": {"value": bmi, "unit": "kg/m2", "version": CALCULATION_VERSIONS["bmi"]},
        "waist_hip_ratio": {"value": whr, "unit": "ratio", "version": CALCULATION_VERSIONS["waist_hip_ratio"]},
        "weight_change": {"value": change, "unit": "kg", "version": CALCULATION_VERSIONS["weight_change"]},
        "measurement_source_id": latest.source_id if latest else None,
    }


def assessment_fingerprint(client_id: str, sources: list[AssessmentSource], calculations: dict[str, Any]) -> str:
    canonical = {
        "client_id": client_id,
        "sources": [source.model_dump(mode="json") for source in sorted(sources, key=lambda row: (row.source_type, row.source_id, row.source_version))],
        "calculations": calculations,
    }
    return sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_manifest(sources: list[AssessmentSource]) -> list[dict[str, Any]]:
    return [{
        "source_type": source.source_type,
        "source_id": source.source_id,
        "source_version": source.source_version,
        "status": source.status,
        "observed_at": source.observed_at.isoformat() if source.observed_at else None,
        "provenance": source.provenance,
    } for source in sources]


REQUIRED_PROFILE_FIELDS = (
    "dietary_preference", "meal_timing_frequency", "typical_dietary_intake",
    "appetite_eating_patterns", "water_intake",
)


def diet_plan_readiness(profile: NutritionProfile, sources: list[AssessmentSource], *,
                        workflow_status: str, stale: bool = False,
                        clinical_safety_findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    source_types = {source.get("source_type") if isinstance(source, dict) else source.source_type for source in sources}
    missing = [field for field in REQUIRED_PROFILE_FIELDS if not getattr(profile, field)]
    checklist = {
        "profile_complete": not missing,
        "body_measurement_available": "MEASUREMENT" in source_types,
        "dietary_preference_reviewed": bool(profile.dietary_preference),
        "allergy_restriction_reviewed": "ALLERGIES" in source_types,
        "medical_history_reviewed": "MEDICAL_HISTORY" in source_types,
        "nutrition_assessment_complete": not missing,
        "consultant_review_complete": workflow_status == "REVIEWED",
    }
    if not sources and not any(profile.model_dump().values()):
        outcome = "NOT_STARTED"
    elif stale or clinical_safety_findings or profile.dietary_preference == "VEGAN":
        outcome = "BLOCKED"
    elif missing or not checklist["allergy_restriction_reviewed"] or not checklist["medical_history_reviewed"]:
        outcome = "INCOMPLETE"
    elif workflow_status != "REVIEWED":
        outcome = "NEEDS_REVIEW"
    else:
        outcome = "READY"
    blockers = list(missing)
    if not checklist["allergy_restriction_reviewed"]: blockers.append("allergy_restriction_review")
    if not checklist["medical_history_reviewed"]: blockers.append("medical_history_review")
    if profile.dietary_preference == "VEGAN": blockers.append("vegan_food_engine_not_supported")
    if stale: blockers.append("assessment_sources_changed")
    if clinical_safety_findings: blockers.append("clinical_safety_review")
    return {"outcome": outcome, "checklist": checklist, "outstanding_information": blockers,
            "operational_only": True, "clinical_safety_guarantee": False}
