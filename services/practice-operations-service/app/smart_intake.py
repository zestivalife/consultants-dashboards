"""MP-010 External client intake synchronisation and selective update contracts.

The registry is intentionally code-versioned: links contain only opaque tokens and
field identifiers, while labels, validation and canonical destinations remain
server authoritative.  No client response can approve a professional decision.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


FIELD_SCHEMA_VERSION = 2
FIELD_STATUSES = {
    "CAPTURED", "MISSING", "INVALID", "REQUIRES_CONFIRMATION", "NOT_APPLICABLE",
    "DECLINED", "PENDING_CLIENT", "PENDING_CONSULTANT_REVIEW", "CONFIRMED",
}
ACTIVE_REQUEST_STATES = {"CREATED", "SENT", "OPENED", "PARTIALLY_COMPLETED", "SUBMITTED"}

# Actual v2 intake keys mapped to the existing NutritionProfile contract.  Fields
# outside this registry remain in their existing intake/profile owner and are not
# copied into a second clinical store.
FIELD_REGISTRY: dict[str, dict[str, Any]] = {
    "dietary_preference": {"label": "Dietary preference", "section": "Nutrition", "path": ("nutrition", "dietPreference"), "assessment": "dietary_preference", "required": True, "kind": "enum", "options": ["VEGETARIAN", "EGGITARIAN", "EGG", "NON_VEGETARIAN", "VEGAN"]},
    "allergy_status": {"label": "Allergy status", "section": "Allergies", "path": ("allergiesFamilyHistory", "hasAllergies"), "assessment": "allergies_intolerances", "required": True, "kind": "enum", "options": ["YES", "NO", "NOT_SURE"]},
    "food_allergies": {"label": "Food allergies", "section": "Allergies", "path": ("allergiesFamilyHistory", "foodAllergies"), "assessment": "allergies_intolerances", "required": False, "kind": "list", "options": ["MILK_DAIRY", "PEANUTS", "TREE_NUTS", "EGG", "WHEAT", "SOY", "FISH", "SHELLFISH", "OTHER"], "depends_on": ("allergy_status", "YES")},
    "food_restrictions": {"label": "Food restrictions", "section": "Nutrition", "path": ("nutrition", "restrictions"), "assessment": "food_restrictions", "required": False, "kind": "list", "options": ["JAIN", "NO_ONION_GARLIC", "NO_DAIRY", "GLUTEN_FREE", "NO_ADDED_SUGAR", "LOW_SODIUM", "HALAL", "FASTING_PRACTICES", "NONE", "OTHER"]},
    "meal_timing_frequency": {"label": "Meals per day", "section": "Nutrition", "path": ("nutrition", "mealsPerDay"), "assessment": "meal_timing_frequency", "required": True, "kind": "enum", "options": ["1", "2", "3", "4", "5_PLUS"]},
    "typical_dietary_intake": {"label": "Typical dietary intake", "section": "Nutrition", "path": ("nutrition", "typicalDietaryIntake"), "assessment": "typical_dietary_intake", "required": True, "kind": "enum", "options": ["HOME_COOKED", "MIXED_HOME_OUTSIDE", "FREQUENT_RESTAURANT", "REGULAR_SNACKING", "IRREGULAR_SCHEDULE"]},
    "appetite_eating_patterns": {"label": "Appetite and eating patterns", "section": "Nutrition", "path": ("nutrition", "skipMeals"), "assessment": "appetite_eating_patterns", "required": True, "kind": "list", "options": ["NORMAL_APPETITE", "LOW_APPETITE", "HIGH_APPETITE", "IRREGULAR_HUNGER", "SKIPS_MEALS", "LATE_NIGHT_EATING", "FREQUENT_SNACKING", "EMOTIONAL_EATING", "NONE", "OTHER"]},
    "water_intake": {"label": "Daily water intake", "section": "Lifestyle", "path": ("activityHydration", "waterIntakeMl"), "assessment": "water_intake", "required": True, "kind": "water", "options": list(range(1000, 6001, 500))},
    "medical_conditions": {"label": "Medical conditions", "section": "Medical history", "path": ("conditionsSymptoms", "conditions"), "assessment": "nutrition_medical_conditions", "required": True, "kind": "list", "options": ["DIABETES", "PRE_DIABETES", "THYROID_CONDITION", "PCOS", "HYPERTENSION", "HIGH_CHOLESTEROL", "HEART_CONDITION", "STROKE_HISTORY", "ANAEMIA", "ASTHMA", "ARTHRITIS", "KIDNEY_CONDITION", "LIVER_CONDITION", "DIGESTIVE_CONDITION", "OTHER", "NONE", "NOT_SURE"]},
    "medications": {"label": "Current medications", "section": "Medical history", "path": ("medicationsSupplements", "medications"), "assessment": "relevant_medications", "required": False, "kind": "list"},
    "supplements": {"label": "Current supplements", "section": "Medical history", "path": ("medicationsSupplements", "supplementTypes"), "assessment": "relevant_supplements", "required": False, "kind": "list", "options": ["VITAMIN_D", "VITAMIN_B12", "CALCIUM", "IRON", "MULTIVITAMIN", "OMEGA_3", "PROTEIN", "PROBIOTIC", "OTHER", "NONE"]},
    "health_goals": {"label": "Health goals", "section": "Goals", "path": ("goals", "goals"), "assessment": "weight_management_goals", "required": True, "kind": "list", "options": ["LOSE_WEIGHT", "GAIN_WEIGHT", "GAIN_MUSCLE", "MAINTAIN_WEIGHT", "BLOOD_SUGAR", "PCOS", "THYROID", "CHOLESTEROL", "BLOOD_PRESSURE", "DIGESTIVE_HEALTH", "MORE_ENERGY", "BETTER_SLEEP", "BETTER_FITNESS", "BETTER_EATING_HABITS", "GENERAL_WELLNESS"]},
}

WEIGHT_GOALS = {"LOSE_WEIGHT", "GAIN_WEIGHT", "GAIN_MUSCLE", "MAINTAIN_WEIGHT"}
ASSESSMENT_FIELDS = (
    "dietary_preference", "allergies_intolerances", "food_restrictions",
    "meal_timing_frequency", "typical_dietary_intake", "appetite_eating_patterns",
    "water_intake", "food_dislikes_preferences", "nutrition_medical_conditions",
    "relevant_medications", "relevant_supplements", "weight_management_goals",
    "recovery_disease_management_goals", "consultant_notes",
)


class InformationRequestCreate(BaseModel):
    field_ids: list[str] = Field(min_length=1, max_length=len(FIELD_REGISTRY))
    expires_in_hours: int = Field(default=168, ge=1, le=720)
    delivery_channel: Literal["COPY_LINK", "EMAIL", "WHATSAPP"] = "COPY_LINK"

    @field_validator("field_ids")
    @classmethod
    def fields_are_client_editable(cls, value: list[str]) -> list[str]:
        unique = list(dict.fromkeys(value))
        unknown = set(unique) - set(FIELD_REGISTRY)
        if unknown:
            raise ValueError(f"Unsupported client field identifiers: {', '.join(sorted(unknown))}")
        return unique


class InformationRequestPatch(BaseModel):
    expected_version: int = Field(ge=1)
    values: dict[str, Any] = Field(default_factory=dict, max_length=len(FIELD_REGISTRY))

    @model_validator(mode="after")
    def validate_values(self):
        unknown = set(self.values) - set(FIELD_REGISTRY)
        if unknown:
            raise ValueError("Submitted values contain fields outside the approved request scope")
        for key, value in self.values.items():
            validate_field_value(key, value)
        return self


class InformationRequestReview(BaseModel):
    expected_version: int = Field(ge=1)
    decisions: dict[str, Literal["CONFIRM", "REQUEST_CLARIFICATION"]]
    notes: str | None = Field(default=None, max_length=4000)


def _value(source: dict[str, Any], path: tuple[str, str]) -> Any:
    parent = source.get(path[0])
    return parent.get(path[1]) if isinstance(parent, dict) else None


def is_present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _first(source: dict[str, Any], *paths: tuple[str, str]) -> Any:
    for path in paths:
        value = _value(source, path)
        if is_present(value) or value == 0 or value is False:
            return value
    return None


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return [] if not is_present(value) else [str(value)]
    result = []
    for item in value:
        if isinstance(item, dict):
            candidate = item.get("name") or item.get("code") or item.get("value")
        else:
            candidate = item
        if candidate is not None and str(candidate).strip():
            result.append(str(candidate).strip())
    return result


def _single_choice(value: Any) -> str | None:
    """Accept legacy single-choice answers persisted as one-item lists."""
    if isinstance(value, list):
        values = _strings(value)
        return values[0] if values else None
    if isinstance(value, dict):
        values = _strings([value])
        return values[0] if values else None
    return str(value).strip() if value is not None and str(value).strip() else None


def canonical_assessment_values(canonical: dict[str, Any]) -> dict[str, Any]:
    """Map the persisted 14-step intake contract into NutritionProfile values."""
    nutrition = canonical.get("nutrition") if isinstance(canonical.get("nutrition"), dict) else {}
    allergy_status = _single_choice(_first(canonical, ("allergiesFamilyHistory", "hasAllergies")))
    allergies = _strings(_first(canonical, ("allergiesFamilyHistory", "foodAllergies")))
    if allergy_status in {"NO", "NOT_SURE"} and not allergies:
        allergies = [allergy_status]
    diet = _single_choice(_first(canonical, ("nutrition", "dietPreference")))
    if diet == "EGGITARIAN":
        diet = "EGG"
    meals = _first(canonical, ("nutrition", "mealsPerDay"))
    skip = _single_choice(_first(canonical, ("nutrition", "skipMeals")))
    eating_patterns = []
    if skip == "NEVER":
        eating_patterns = ["NONE"]
    elif skip in {"SOMETIMES", "OFTEN"}:
        eating_patterns = ["SKIPS_MEALS"] + _strings(nutrition.get("skippedMeals"))
    typical = _first(canonical, ("nutrition", "typicalDietaryIntake"))
    if not is_present(typical):
        meals_payload = {key: nutrition.get(key) for key in ("breakfast", "lunch", "dinner", "snacks") if is_present(nutrition.get(key))}
        typical = "; ".join(f"{key}: {', '.join(_strings(value))}" for key, value in meals_payload.items()) or None
    water_ml = _first(canonical, ("activityHydration", "waterIntakeMl"))
    water = f"{float(water_ml) / 1000:g} L/day" if isinstance(water_ml, (int, float)) else None
    medications = _strings(_first(canonical, ("medicationsSupplements", "medications")))
    supplements = _strings(_first(canonical, ("medicationsSupplements", "supplementTypes"), ("medicationsSupplements", "supplements")))
    conditions = _strings(_first(canonical, ("conditionsSymptoms", "conditions"), ("medicalHistory", "conditions")))
    goals = _strings(_first(canonical, ("goals", "goals"), ("goals", "selectedGoals")))
    return {
        "dietary_preference": diet,
        "allergies_intolerances": allergies,
        "food_restrictions": _strings(_first(canonical, ("nutrition", "restrictions"))),
        "meal_timing_frequency": str(meals) if is_present(meals) else None,
        "typical_dietary_intake": typical,
        "appetite_eating_patterns": eating_patterns,
        "water_intake": water,
        "food_dislikes_preferences": _strings(_first(canonical, ("nutrition", "foodDislikesPreferences"), ("nutrition", "foodDislikes"))),
        "nutrition_medical_conditions": conditions,
        "relevant_medications": medications,
        "relevant_supplements": supplements,
        "weight_management_goals": [goal for goal in goals if goal in WEIGHT_GOALS],
        "recovery_disease_management_goals": [goal for goal in goals if goal not in WEIGHT_GOALS],
    }


def resolve_assessment(canonical: dict[str, Any], assessment: dict[str, Any] | None = None,
                       *, intake_updated_at: datetime | None = None,
                       professionally_confirmed: bool = False) -> dict[str, Any]:
    """Resolve intake defaults without overwriting any consultant-authored value."""
    intake_values = canonical_assessment_values(canonical)
    assessment = dict(assessment or {})
    values: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    for field in ASSESSMENT_FIELDS:
        professional = assessment.get(field)
        intake = intake_values.get(field)
        if is_present(professional) or professional == 0 or professional is False:
            values[field] = professional
            provenance[field] = {"source": "CONSULTANT_CONFIRMED" if professionally_confirmed else "CONSULTANT_ASSESSMENT", "confirmed": professionally_confirmed}
        elif is_present(intake) or intake == 0 or intake is False:
            values[field] = intake
            provenance[field] = {"source": "CLIENT_SUBMITTED", "confirmed": False, "captured_at": intake_updated_at.isoformat() if intake_updated_at else None}
        else:
            values[field] = professional if professional is not None else ([] if field in {"allergies_intolerances", "food_restrictions", "nutrition_medical_conditions", "relevant_medications", "relevant_supplements", "weight_management_goals", "recovery_disease_management_goals"} else None)
            provenance[field] = {"source": None, "confirmed": False}
    return {"assessment_data": values, "field_provenance": provenance}


def validate_field_value(field_id: str, value: Any) -> None:
    rule = FIELD_REGISTRY[field_id]
    if value is None or value == "":
        raise ValueError(f"{rule['label']} cannot be blank")
    if rule["kind"] == "enum" and value not in rule["options"]:
        raise ValueError(f"{rule['label']} has an unsupported value")
    if rule["kind"] == "list" and not isinstance(value, list):
        raise ValueError(f"{rule['label']} must be a list")
    if rule["kind"] == "water" and (not isinstance(value, (int, float)) or value not in rule["options"]):
        raise ValueError(f"{rule['label']} must be selected in 0.5 litre increments from 1 to 6 litres")
    if isinstance(value, str) and len(value) > 8000:
        raise ValueError(f"{rule['label']} is too long")


def resolve_completeness(canonical: dict[str, Any], *, pending_fields: set[str] | None = None,
                         review_fields: set[str] | None = None, confirmed_fields: set[str] | None = None,
                         updated_at: datetime | None = None) -> dict[str, Any]:
    pending_fields, review_fields, confirmed_fields = pending_fields or set(), review_fields or set(), confirmed_fields or set()
    rows = []
    for field_id, rule in FIELD_REGISTRY.items():
        value = _value(canonical, rule["path"])
        if field_id == "typical_dietary_intake" and not is_present(value):
            nutrition = canonical.get("nutrition") if isinstance(canonical.get("nutrition"), dict) else {}
            value = next((nutrition.get(key) for key in ("breakfast", "lunch", "dinner", "snacks") if is_present(nutrition.get(key))), None)
        elif field_id == "medical_conditions" and not is_present(value):
            value = _value(canonical, ("medicalHistory", "conditions"))
        elif field_id == "health_goals" and not is_present(value):
            value = _value(canonical, ("goals", "selectedGoals"))
        dependency = rule.get("depends_on")
        applicable = not dependency or _value(canonical, FIELD_REGISTRY[dependency[0]]["path"]) == dependency[1]
        if not applicable:
            status, reason = "NOT_APPLICABLE", "The preceding answer makes this field not applicable."
        elif field_id in review_fields:
            status, reason = "PENDING_CONSULTANT_REVIEW", "The client supplied an update that requires professional review."
        elif field_id in confirmed_fields:
            status, reason = "CONFIRMED", None
        elif field_id in pending_fields:
            status, reason = "PENDING_CLIENT", "A secure client update is outstanding."
        elif is_present(value):
            status, reason = "CAPTURED", None
        elif rule["required"]:
            status, reason = "MISSING", "Required for Nutrition Assessment readiness."
        else:
            status, reason = "MISSING", "Optional information has not been provided."
        rows.append({"field_id": field_id, "label": rule["label"], "section": rule["section"],
                     "status": status, "current_value": value, "source": "CLIENT_INTAKE" if is_present(value) else None,
                     "last_updated_at": updated_at.isoformat() if updated_at else None,
                     "requirement_level": "REQUIRED" if rule["required"] else "OPTIONAL", "reason": reason,
                     "client_can_provide": True, "consultant_confirmation_required": field_id in {"allergy_status", "food_allergies", "medical_conditions", "medications"},
                     "blocks_readiness": bool(rule["required"] and status not in {"CAPTURED", "CONFIRMED", "NOT_APPLICABLE"})})
    counts = {status: sum(row["status"] == status for row in rows) for status in FIELD_STATUSES}
    blockers = [row["field_id"] for row in rows if row["blocks_readiness"]]
    return {"schema_version": FIELD_SCHEMA_VERSION, "fields": rows, "counts": counts,
            "total_relevant": sum(row["status"] != "NOT_APPLICABLE" for row in rows),
            "readiness": "NEEDS_INFORMATION" if blockers else "NEEDS_CONSULTANT_REVIEW",
            "blocking_fields": blockers}


def scoped_patch(existing: dict[str, Any], submitted: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    """Return a field-level merge; absent inputs never clear prior answers."""
    result = {key: dict(value) if isinstance(value, dict) else value for key, value in existing.items()}
    for field_id, value in submitted.items():
        if field_id not in allowed:
            raise ValueError("Submitted field is outside this request")
        validate_field_value(field_id, value)
        section, key = FIELD_REGISTRY[field_id]["path"]
        result.setdefault(section, {})[key] = value
    return result
