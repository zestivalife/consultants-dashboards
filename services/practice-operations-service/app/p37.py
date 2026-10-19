"""P37 deterministic requirement and readiness projection helpers."""

ITEM_ORDER = ("PROFILE", "INTAKE", "CONSENT", "ASSESSMENT", "DOCUMENTS", "APPOINTMENT", "PAYMENT", "PORTAL", "QUESTIONS")
BLOCKERS = {
    "PROFILE": "CLIENT_PROFILE_INCOMPLETE",
    "INTAKE": "REQUIRED_INTAKE_PENDING",
    "CONSENT": "CONSENT_PENDING",
    "ASSESSMENT": "REQUIRED_ASSESSMENT_PENDING",
    "DOCUMENTS": "REQUIRED_DOCUMENT_PENDING",
    "APPOINTMENT": "APPOINTMENT_NOT_CONFIRMED",
    "PORTAL": "PORTAL_ACCESS_NOT_ESTABLISHED",
    "QUESTIONS": "PRE_SESSION_QUESTIONS_PENDING",
}


def resolve_requirements(profession_code, capabilities, overrides=None):
    """Return a bounded profession-aware policy; optional work never blocks."""
    capabilities = set(capabilities or ())
    requirements = {
        "PROFILE": {"required": True},
        "INTAKE": {"required": True},
        "CONSENT": {"required": True},
        "ASSESSMENT": {"required": "ASSESSMENTS" in capabilities},
        "DOCUMENTS": {"required": False, "requests": []},
        "APPOINTMENT": {"required": True},
        "PAYMENT": {"required": False, "informational": True},
        "PORTAL": {"required": "CLIENT_PORTAL" in capabilities},
        "QUESTIONS": {"required": False},
    }
    for key, value in (overrides or {}).items():
        if key in requirements and isinstance(value, dict):
            requirements[key] = {**requirements[key], **value}
    requirements["profession_code"] = profession_code
    return requirements


def project_readiness(requirements, facts):
    items = []
    required_total = required_complete = 0
    blockers = []
    failed = False
    for key in ITEM_ORDER:
        policy = requirements.get(key, {})
        required = bool(policy.get("required"))
        fact = facts.get(key, {})
        state = fact.get("state", "NOT_REQUIRED" if not required else "PENDING")
        if state == "FAILED":
            failed = True
        if required:
            required_total += 1
            if state == "COMPLETE":
                required_complete += 1
            elif state != "FAILED":
                blockers.append(BLOCKERS.get(key, f"{key}_PENDING"))
        items.append({"key": key, "required": required, "state": state, "detail": fact.get("detail")})
    percentage = 100 if required_total == 0 else (required_complete * 100) // required_total
    ready = not failed and required_complete == required_total
    return {"state": "FAILED" if failed else "READY", "items": items, "requiredComplete": required_complete,
            "requiredTotal": required_total, "readinessPercent": percentage, "blockers": blockers,
            "readyForConsultation": ready, "lifecycleState": "READY_FOR_CONSULTATION" if ready else "ONBOARDING_IN_PROGRESS"}
