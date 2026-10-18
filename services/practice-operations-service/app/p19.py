"""P19 referral state, consent, and sharing policy."""

ALLOWED_SCOPES=frozenset({"BASIC_PROFILE","CONTACT_DETAILS","PUBLISHED_PLAN","ASSESSMENT_SUMMARY","PROGRESS_SUMMARY","SELECTED_HEALTH_RECORDS","SELECTED_DOCUMENTS","GOALS"})
FORBIDDEN_SCOPES=frozenset({"PRIVATE_NOTES","RAW_SESSION_NOTES","INTERNAL_INTELLIGENCE","BILLING","TEAM_NOTES"})
TRANSITIONS={
    "REQUEST_CONSENT":{"DRAFT":"CONSENT_PENDING"},"SEND":{"READY_TO_SEND":"SENT"},
    "ACCEPT":{"SENT":"ACCEPTED"},"DECLINE":{"SENT":"DECLINED"},
    "COMPLETE":{"ACCEPTED":"COMPLETED"},"CANCEL":{"DRAFT":"CANCELLED","CONSENT_PENDING":"CANCELLED","READY_TO_SEND":"CANCELLED","SENT":"CANCELLED"},
}

def validate_scopes(scopes):
    requested=set(scopes)
    if requested & FORBIDDEN_SCOPES or requested-ALLOWED_SCOPES:
        raise ValueError("One or more referral data scopes are not permitted")
    return sorted(requested)

def referral_transition(status,action):
    target=TRANSITIONS.get(action,{}).get(status)
    if not target:raise ValueError("Referral transition is not permitted")
    return target

