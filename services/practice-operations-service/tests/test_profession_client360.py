from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_profession_client360_is_read_only_and_tenant_scoped():
    source=(ROOT/'app/main.py').read_text()
    route='clients/{client_id}/profession-view'
    block=source[source.index(route):source.index('@app.get("/api/v1/profession-intake/{token}")')]
    assert 'external_only(request, ctx)' in block
    assert 'tenant_id=:tenant' in block
    assert 'INSERT INTO' not in block
    assert 'UPDATE ' not in block
    assert 'DELETE FROM' not in block

def test_each_authorised_profession_has_a_real_projection():
    source=(ROOT/'app/main.py').read_text()
    for profession in ('DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST'):
        assert f'"{profession}":' in source
    for source_name in ('assessments','consultations','follow-ups','goals','tasks','notes'):
        assert f'"{source_name}"' in source

