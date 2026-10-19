from pathlib import Path
import pytest
from app.p39 import experience_label, public_review_eligible, validate_ratings

ROOT=Path(__file__).parents[1]
MAIN=(ROOT/'app/main.py').read_text()
MIGRATION=(ROOT/'alembic/versions/0039_client_experience_feedback.py').read_text()

def test_experience_labels_are_operational_not_clinical():
    assert [experience_label(v) for v in (1,3,5,None)]==['NEEDS_ATTENTION','NEUTRAL','POSITIVE','INSUFFICIENT_DATA']

def test_public_review_eligibility_is_rating_neutral():
    assert public_review_eligible(submitted=True,verified_engagement=True,invitation_enabled=True)
    assert 'rating' not in public_review_eligible.__code__.co_varnames
    assert not public_review_eligible(submitted=False,verified_engagement=True,invitation_enabled=True)

def test_rating_validation_is_bounded():
    assert validate_ratings({'overall_experience':5})['overall_experience']==5
    with pytest.raises(ValueError):validate_ratings({'overall_experience':0})

def test_external_only_expand_migration_and_immutable_submission():
    assert '0038_post_consultation' in MIGRATION
    for table in ('external_client_feedback_requests','external_client_feedback_submissions','external_client_feedback_actions','external_client_feedback_audit_events'):
        assert f'CREATE TABLE {table}' in MIGRATION
    assert 'request_id UUID NOT NULL UNIQUE' in MIGRATION
    assert 'external_consultant_reviews' not in MIGRATION
    assert 'ALTER TABLE' not in MIGRATION

def test_completed_session_exact_scope_and_immutable_contract():
    assert 'COMPLETED_SESSION_REQUIRED' in MAIN
    assert "session[\"status\"]!=\"COMPLETED\"" in MAIN
    assert 'tenant_id=:tenant AND client_id=:client' in MAIN
    assert 'FEEDBACK_IMMUTABLE' in MAIN

def test_no_auto_send_public_review_write_or_duplicate_grievance():
    p39=MAIN[MAIN.index('# P39 private client-experience feedback.'):MAIN.index('# P31 Consultant Marketplace')]
    assert '"autoSend":False' in p39 and '"publicReviewCreated":False' in p39
    assert 'GRIEVANCE_REFERENCE_REQUIRED' in p39
    assert 'INSERT INTO external_consultant_reviews' not in p39
    assert 'INSERT INTO external_client_grievance' not in p39

def test_analytics_dimensions_are_separate():
    for value in ('overall_experience','communication','professionalism','booking_experience','support_experience','response_rate'):
        assert value in MAIN
    assert '"serviceOutcomeScore":None' in MAIN
