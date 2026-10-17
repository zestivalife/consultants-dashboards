from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_assessment_migration_is_additive_external_only():
    source=(ROOT/'alembic/versions/0005_assessment_engine.py').read_text()
    tables=('external_assessment_definitions','external_assessment_versions','external_assessment_questions','external_assessment_instances','external_assessment_answers','external_assessment_scores','external_assessment_review_events')
    for table in tables: assert f'CREATE TABLE {table}' in source
    assert 'ALTER TABLE' not in source
    assert 'diet' not in source.lower()

def test_assessment_routes_are_tenant_and_capability_scoped():
    source=(ROOT/'app/main.py').read_text()
    for route in ('assessments/definitions','clients/{client_id}/assessments','assessments/{assessment_id}','assessments/{assessment_id}/complete'): assert route in source
    assert 'require_capability(request,db,ctx,"ASSESSMENTS")' in source
    assert 'tenant_id=:tenant' in source

def test_system_templates_cover_each_authorised_p2_profession():
    source=(ROOT/'alembic/versions/0005_assessment_engine.py').read_text()
    for profession in ('DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST'): assert profession in source
