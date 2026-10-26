from pathlib import Path
import pytest
from app.marketplace import (ADMIN_ACTIONS,PRIVATE_FIELDS,ProfileSave,assert_transition,can_publish,
                             completeness,dedupe_key,public_projection,public_rating,publicly_visible,slug_base)

ROOT=Path(__file__).parents[1]

def payload():return {"display_name":"Priya Sharma","professional_title":"Health Coach","profession_code":"HEALTH_COACH","profile_photo_url":"https://cdn.example/photo.jpg","specialisations":["Habits"],"experience_years":8,"previous_workplaces":["Demo Wellness Centre"],"bio":"A sufficiently detailed professional public biography.","languages":["English"],"consultation_modes":["ONLINE"],"areas_of_focus":["Sleep"],"public_locations":[],"services":[{"name":"Coaching"}],"programmes":[],"session_duration":60,"public_fee_from":250000,"accepting_new_clients":True}

def test_public_projection_allowlist_excludes_every_private_field():
    source={**payload(),**{key:"secret" for key in PRIVATE_FIELDS}}
    projection=public_projection(source)
    assert not (set(projection)&PRIVATE_FIELDS)
    assert projection["display_name"]=="Priya Sharma"
    assert projection["previous_workplaces"]==["Demo Wellness Centre"]

def test_completeness_is_deterministic_and_requires_a_qualification_for_review():
    score,missing=completeness(payload(),0)
    assert score==90 and missing==["Qualification added"]
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

def test_platform_context_can_be_tenantless_but_ordinary_roles_cannot():
    main=(ROOT/"app/main.py").read_text()
    context_section=main[main.index("def context("):main.index("def external_only")]
    assert '{"SUPER_ADMIN","SUPERUSER","PLATFORM_OWNER"}' in context_section
    assert 'if not x_tenant_id and role not in' in context_section
    assert 'tenant_id": x_tenant_id' in context_section

def test_super_admin_inventory_is_platform_guarded_and_includes_not_started():
    main=(ROOT/"app/main.py").read_text()
    section=main[main.index('@app.get("/api/v1/practice-operations/admin/marketplace/consultants")'):main.index('@app.put("/api/v1/practice-operations/admin/marketplace/profiles/')]
    assert "denied=_platform_admin(request,ctx)" in section
    assert 'status=profile["status"] if profile else "NOT_STARTED"' in section
    for value in ["ELIGIBLE_TO_SUBMIT","NOT_ELIGIBLE","UNDER_REVIEW","APPROVED_NOT_PUBLISHED","PUBLIC","SUSPENDED","DIRECTORY_ONLY","DIRECTORY_AND_HOMEPAGE"]:assert value in section

def test_enrolment_reuses_p24_and_reviews_require_completed_engagement():
    main=(ROOT/"app/main.py").read_text()
    assert "'PUBLIC_CONSULTANT_DIRECTORY'" in main
    assert "INSERT INTO external_leads" in main
    assert "external_scheduled_appointments" in main
    assert 'status=\'COMPLETED\'' in main
    assert "REVIEW_NOT_ELIGIBLE" in main

def test_real_data_contract_rejects_private_photo_and_requires_governed_catalog_shape():
    good=payload()|{"public_locations":[{"id":"00000000-0000-0000-0000-000000000001","name":"QA Clinic","mode":"IN_PERSON"}],"services":[{"id":"00000000-0000-0000-0000-000000000002","name":"QA Session","description":"Fixture only","duration":60,"mode":"IN_PERSON","location_id":"00000000-0000-0000-0000-000000000001","fee":10000,"enrolment_mode":"REQUEST_ENROLMENT","active":True}],"programmes":[{"id":"00000000-0000-0000-0000-000000000003","name":"QA Programme","description":"Fixture only","fee":50000,"active":True}]}
    assert ProfileSave(**good).services[0].duration==60
    with pytest.raises(ValueError):ProfileSave(**(good|{"profile_photo_url":"https://private.example/image?X-Amz-Signature=secret"}))

def test_complete_super_admin_lifecycle_keeps_approval_and_publication_separate():
    path=[("DRAFT","SUBMITTED_FOR_REVIEW"),("SUBMITTED_FOR_REVIEW","UNDER_REVIEW"),("UNDER_REVIEW","CHANGES_REQUIRED"),("CHANGES_REQUIRED","DRAFT"),("DRAFT","SUBMITTED_FOR_REVIEW"),("SUBMITTED_FOR_REVIEW","UNDER_REVIEW"),("UNDER_REVIEW","APPROVED"),("APPROVED","PUBLISHED"),("PUBLISHED","UNPUBLISHED"),("UNPUBLISHED","PUBLISHED"),("PUBLISHED","SUSPENDED"),("SUSPENDED","UNPUBLISHED")]
    for current,target in path:assert_transition(current,target)
    approved={"status":"APPROVED","public_visibility":False,"approval_valid":True,"approved_version":2,"working_version":2,"suspended_at":None}
    assert can_publish(approved) and not publicly_visible(approved)

def test_super_admin_can_publish_a_submitted_profile_in_one_governed_decision():
    assert_transition("SUBMITTED_FOR_REVIEW","PUBLISHED")
    assert ADMIN_ACTIONS["PUBLISH_SUBMISSION"]=="PUBLISHED"

def test_marketplace_decision_casts_reused_status_bind_for_asyncpg():
    main=(ROOT/"app/main.py").read_text()
    section=main[main.index('async def admin_marketplace_decision'):main.index('@app.post("/api/v1/practice-operations/admin/marketplace/qualifications/')]
    assert "status=CAST(:status AS VARCHAR)" in section
    assert "CASE WHEN CAST(:status AS VARCHAR)='APPROVED'" in section
    assert "CASE WHEN CAST(:status AS VARCHAR)='PUBLISHED'" in section

def test_super_admin_cannot_approve_or_publish_without_verified_qualification():
    main=(ROOT/"app/main.py").read_text()
    section=main[main.index('async def admin_marketplace_decision'):main.index('@app.post("/api/v1/practice-operations/admin/marketplace/qualifications/')]
    assert 'action in {"APPROVE_PROFILE","PUBLISH_PROFILE","PUBLISH_SUBMISSION"}' in section
    assert 'VERIFIED_QUALIFICATION_REQUIRED' in section

def test_rating_includes_only_published_verified_engagements_and_never_zero_stars():
    reviews=[{"overall_rating":5,"verified_engagement":True,"status":"PUBLISHED"},{"overall_rating":1,"verified_engagement":False,"status":"PUBLISHED"},{"overall_rating":2,"verified_engagement":True,"status":"HIDDEN"}]
    assert public_rating(reviews)=={"review_count":1,"average_rating":5.0,"label":"5.0"}
    assert public_rating([])=={"review_count":0,"average_rating":None,"label":"New on Zestiva"}

def test_operational_endpoints_cover_readiness_credentials_reviews_and_enrolments():
    main=(ROOT/"app/main.py").read_text()
    for route in ["/marketplace/readiness","/marketplace/reviews","/admin/marketplace/operations"]:assert route in main
    for domain in ["external_service_packages","external_appointment_types","external_practice_locations","external_availability_rules","external_documents"]:assert domain in main[main.index('async def marketplace_readiness'):main.index('@app.put("/api/v1/practice-operations/marketplace/profile")')]
    assert '"EXPIRE_QUALIFICATION":"EXPIRED"' in main

def test_directory_filters_are_bounded_composable_and_privacy_safe():
    main=(ROOT/"app/main.py").read_text()
    section=main[main.index('@app.get("/api/v1/public/consultants")'):main.index('@app.get("/api/v1/public/consultants/{slug}")')]
    for parameter in ["profession:list[str]","specialisation:list[str]","mode:list[str]","location:list[str]","language:list[str]","experience_min:int","experience_max:int","availability:str","rating_min:float","fee_min:int","fee_max:int","fee_currency:str","accepting_new_clients:bool","service:list[str]","page:int","page_size:int"]:
        assert parameter in section
    for contract in ["=ANY(:professions)","=ANY(:specialisations)","=ANY(:modes)","=ANY(:locations)","=ANY(:languages)","r.review_count>0","external_availability_rules","LIMIT :limit OFFSET :offset","FEE_CURRENCY_REQUIRED","CONFIRMED_EMPTY"]:
        assert contract in section
    assert 'item.pop("_tenant_id",None)' in main

def test_directory_sorting_is_deterministic_and_non_clinical():
    main=(ROOT/"app/main.py").read_text()
    section=main[main.index('@app.get("/api/v1/public/consultants")'):main.index('@app.get("/api/v1/public/consultants/{slug}")')]
    for sort in ["recommended","next_available","rating_desc","most_reviewed","experience_desc","fee_asc","fee_desc"]:assert sort in section
    assert "p.accepting_new_clients DESC" in section
    assert "lower(v.projection->>'display_name') ASC" in section

def test_fixture_import_is_draft_only_repeatable_and_contains_no_reviews():
    fixture=(ROOT.parents[1]/"docs/fixtures/p31-marketplace-profile-drafts.csv").read_text()
    assert fixture.count("P31-QA-")==4
    assert fixture.count(",DRAFT") == 4
    assert "fixture_only" in fixture and "review" not in fixture.lower()

def test_real_consultant_onboarding_checklist_classifies_public_and_private_data():
    checklist=(ROOT.parents[1]/"docs/p31-marketplace-onboarding-checklist.md").read_text()
    for field in ["Identity","Public profile","Photo","Credentials","Services","Locations","Availability","Reviews"]:assert field in checklist
    assert "Derivative only" in checklist and "Source document" in checklist
