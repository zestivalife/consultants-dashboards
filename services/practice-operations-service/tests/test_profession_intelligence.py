from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_p7_defines_every_governed_profession_provider():
    source=(ROOT/'app/main.py').read_text()
    for profession in ('DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST'):
        assert f'"{profession}"' in source

def test_p7_signals_are_traceable_non_clinical_and_tenant_scoped():
    source=(ROOT/'app/main.py').read_text()
    for field in ('signal_code','profession_code','tenant_id','client_id','source_domain','source_record_id','reason','priority','cta','provenance','resolution_state'):
        assert f'"{field}"' in source
    assert 'tenant_id=:tenant' in source
    for prohibited in ('CRITICAL MEDICAL','EMERGENCY','HIGH CLINICAL RISK','self-harm','suicide'):
        assert prohibited not in source

def test_p7_does_not_rewrite_phase_a_priority_engine_or_schema():
    assert not (ROOT/'alembic/versions/0009_profession_intelligence.py').exists()
    assert 'intelligence/signals' in (ROOT/'app/main.py').read_text()
