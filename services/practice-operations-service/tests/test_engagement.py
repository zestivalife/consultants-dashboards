from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_p10_has_explainable_states_without_opaque_score():
    source=(ROOT/'app/main.py').read_text()
    for value in ('HIGH','MODERATE','NEEDS_ATTENTION','INSUFFICIENT_DATA','reasons','last_meaningful_activity','explanation'):assert value in source
    assert 'engagement_score' not in source

def test_p10_retention_indicators_are_operational_and_tenant_scoped():
    source=(ROOT/'app/main.py').read_text()
    for value in ('NO_FUTURE_SESSION','CLIENT_INACTIVE','MULTIPLE_MISSED_SESSIONS','CHECKIN_OVERDUE','GOAL_NOT_UPDATED','PLAN_REVIEW_OVERDUE'):assert value in source
    assert 'tenant_id=:tenant' in source
    assert 'clinical risk assessment' in source

def test_p10_requires_no_schema_mutation():
    assert not (ROOT/'alembic/versions/0011_engagement.py').exists()
    assert 'engagement/projections' in (ROOT/'app/main.py').read_text()
