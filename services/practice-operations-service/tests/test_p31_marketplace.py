from pathlib import Path
import pytest
from app.marketplace import (PRIVATE_FIELDS,ProfileSave,assert_transition,can_publish,
                             completeness,dedupe_key,public_projection,publicly_visible,slug_base)

ROOT=Path(__file__).parents[1]

def payload():return {"display_name":"Priya Sharma","professional_title":"Health Coach","profession_code":"HEALTH_COACH","profile_photo_url":"https://cdn.example/photo.jpg","specialisations":["Habits"],"experience_years":8,"bio":"A sufficiently detailed professional public biography.","languages":["English"],"consultation_modes":["ONLINE"],"areas_of_focus":["Sleep"],"public_locations":[],"services":[{"name":"Coaching"}],"programmes":[],"session_duration":60,"public_fee_from":250000,"accepting_new_clients":True}

def test_public_projection_allowlist_excludes_every_private_field():
    source={**payload(),**{key:"secret" for key in PRIVATE_FIELDS}}
    projection=public_projection(source)
    assert not (set(projection)&PRIVATE_FIELDS)
    assert projection["display_name"]=="Priya Sharma"

def test_completeness_is_deterministic_and_requires_verified_qualification():
    score,missing=completeness(payload(),0)
    assert score==90 and missing==["Verified qualification"]
    assert completeness(payload(),1)==(100,[])

def test_approved_is_not_published_and_visibility_fails_closed():
    approved={"status":"APPROVED","approval_valid":True,"approved_version":2,"working_version":2,"public_visibility":False,"suspended_at":None}
    assert can_publish(approved) is True
    assert publicly_visible(approved) is False
    assert publicly_visible({**approved,"status":"PUBLISHED","public_visibility":True}) is True
    assert publicly_visible({**approved,"status":"PUBLISHED","public_visibility":True,"suspended_at":"now"}) is False

def test_profile_transitions_prevent_self_shortcuts():
    assert_transition("DRAFT","SUBMITTED_FOR_REVIEW")
    with pytest.raises(ValueError):assert_transition("DRAFT","APPROVED")
    with pytest.raises(ValueError):assert_transition("APPROVED","DRAFT")

def test_slug_and_enrolment_dedupe_are_stable():
    assert slug_base("Priya Sharma") == "priya-sharma"
    assert dedupe_key("p","A@B.com","123","s")==dedupe_key("p","a@b.com","123","s")

def test_p31_schema_is_additive_expand_only_and_reuses_governed_domains():
    migration=(ROOT/"alembic/versions/0031_consultant_marketplace.py").read_text()
    assert 'down_revision="0030_compliance_audit"' in migration
    for table in ["external_consultant_public_profiles","external_consultant_public_profile_versions","external_consultant_qualifications","external_consultant_marketplace_enrolments","external_consultant_reviews","external_consultant_review_events","external_consultant_marketplace_events","external_consultant_marketplace_audit_events"]:assert f"CREATE TABLE {table}" in migration
    assert "REFERENCES external_documents" in migration
    assert "REFERENCES external_leads" in migration
    assert "expand-only" in migration

def test_public_routes_fail_closed_and_platform_authority_is_distinct():
    main=(ROOT/"app/main.py").read_text()
    assert 'role not in {"SUPER_ADMIN","SUPERUSER","PLATFORM_OWNER"}' in main
    assert "PRACTICE_OWNER" not in main[main.index("def _platform_admin"):main.index("async def _marketplace_profile")]
    for route in ['/api/v1/public/consultants','/api/v1/public/consultants/{slug}','/api/v1/public/consultants/{slug}/availability','/api/v1/public/consultants/{slug}/enrolments']:assert route in main
    public=main[main.index('def _public_profile_sql'):main.index('@app.post("/api/v1/practice-operations/marketplace/profiles')]
    for guard in ["v.status='PUBLISHED'","p.public_visibility=TRUE","p.approval_valid=TRUE","p.suspended_at IS NULL"]:assert guard in public
    for secret in PRIVATE_FIELDS:assert secret not in public

def test_enrolment_reuses_p24_and_reviews_require_completed_engagement():
    main=(ROOT/"app/main.py").read_text()
    assert "'PUBLIC_CONSULTANT_DIRECTORY'" in main
    assert "INSERT INTO external_leads" in main
    assert "external_scheduled_appointments" in main
    assert 'status=\'COMPLETED\'' in main
    assert "REVIEW_NOT_ELIGIBLE" in main
