"""P39 service-experience policy; never clinical effectiveness scoring."""
FEEDBACK_TYPES={"POST_SESSION_FEEDBACK","PROGRAMME_FEEDBACK","PRACTICE_EXPERIENCE_FEEDBACK","SUPPORT_EXPERIENCE_FEEDBACK","BOOKING_EXPERIENCE_FEEDBACK","ONBOARDING_EXPERIENCE_FEEDBACK","CUSTOM_FEEDBACK"}
CADENCES={"EVERY_SESSION","FIRST_SESSION_ONLY","EVERY_N_SESSIONS","PROGRAMME_MILESTONE","PROGRAMME_END","MANUAL_ONLY"}

def experience_label(rating,threshold=2):
    if rating is None:return "INSUFFICIENT_DATA"
    if rating<=threshold:return "NEEDS_ATTENTION"
    if rating==3:return "NEUTRAL"
    return "POSITIVE"

def public_review_eligible(*,submitted,verified_engagement,invitation_enabled):
    """Neutral eligibility deliberately excludes every rating dimension."""
    return bool(submitted and verified_engagement and invitation_enabled)

def validate_ratings(values):
    if not values.get("overall_experience"):raise ValueError("Overall experience rating is required")
    for name,value in values.items():
        if value is not None and not 1<=value<=5:raise ValueError(f"{name} must be between 1 and 5")
    return values
