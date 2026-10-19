from pathlib import Path
import pytest
from app.finder import FINDER_EVENTS,SUPPORT_TAXONOMY,FinderRequest,explain_and_score
ROOT=Path(__file__).resolve().parents[1];MAIN=(ROOT/'app/main.py').read_text();MIGRATION=(ROOT/'alembic/versions/0035_consultant_finder.py').read_text()
def test_migration_is_external_only_and_linear():
 assert 'down_revision="0034_marketplace_shortlist"' in MIGRATION
 assert 'external_marketplace_finder_config' in MIGRATION and 'external_marketplace_finder_events' in MIGRATION
 assert 'ALTER TABLE' not in MIGRATION
def test_central_taxonomy_is_non_clinical_and_maps_marketplace_professions():
 assert SUPPORT_TAXONOMY['MOVEMENT_REHAB']['professions']==['PHYSIOTHERAPIST']
 assert 'DIABETES_EDUCATOR' in SUPPORT_TAXONOMY['DIABETES_SELF_MANAGEMENT']['professions']
 assert not {'diagnosis','symptoms','medical_history'} & set(FinderRequest.model_fields)
def test_matching_is_deterministic_and_explainable():
 request=FinderRequest(support_area='NUTRITION',mode='ONLINE',languages=['Marathi'],availability='WITHIN_7_DAYS',budget_max=100000,currency='INR',experience_min=5)
 score,reasons=explain_and_score({'consultation_modes':['ONLINE'],'languages':['Marathi'],'public_fee_from':80000,'public_fee_currency':'INR','experience_years':8},request,True)
 assert score>100 and {'Available online','Speaks Marathi','Within your selected fee range','Matches your experience preference'}<=set(reasons)
 assert all('%' not in reason for reason in reasons)
def test_public_match_reuses_strict_projection_and_bounded_server_query():
 section=MAIN[MAIN.index('@app.post("/api/v1/public/consultants/finder/matches")'):MAIN.index('@app.post("/api/v1/public/consultants/finder/events")')]
 assert '_public_profile_sql' in section and 'LIMIT :limit' in section and 'match_reasons' in section
 policy=MAIN[MAIN.index('def _public_profile_sql'):MAIN.index('def _public_marketplace_item')]
 for guard in ["p.status='PUBLISHED'","p.public_visibility=TRUE","p.approval_valid=TRUE","p.suspended_at IS NULL"]:assert guard in policy
def test_analytics_allowlist_and_admin_governance():
 assert {'FINDER_STARTED','FINDER_COMPLETED','FINDER_PROFILE_CLICK','FINDER_ENROL_CLICK','FINDER_BOOK_CLICK'}<=FINDER_EVENTS
 admin=MAIN[MAIN.index('@app.get("/api/v1/practice-operations/admin/marketplace/finder-config")'):MAIN.index('@app.get("/api/v1/practice-operations/admin/marketplace/analytics")')]
 assert '_platform_admin' in admin and 'support_area' in admin
def test_no_ai_or_clinical_scoring_dependency():
 finder=(ROOT/'app/finder.py').read_text().lower()
 for forbidden in ['openai','p29','diagnose','clinical score','medical score']:assert forbidden not in finder
