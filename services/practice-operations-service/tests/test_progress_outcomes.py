from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_progress_migration_is_external_only_and_additive():
    source=(ROOT/'alembic/versions/0008_progress_outcomes.py').read_text()
    for table in ('external_progress_metric_definitions','external_progress_observations','external_progress_targets','external_progress_milestones'):
        assert f'CREATE TABLE {table}' in source
    assert 'ALTER TABLE' not in source

def test_progress_is_tenant_scoped_and_biomarker_reference_only():
    source=(ROOT/'app/main.py').read_text()
    for route in ('clients/{client_id}/progress','progress/metrics','progress/observations','progress/targets','progress/milestones'):
        assert route in source
    assert 'BIOMARKER_REFERENCE_ONLY' in source
    assert 'EXISTING_EXTERNAL_BIOMARKER_HISTORY' in source
    assert 'tenant_id=:tenant' in source

def test_progress_uses_existing_goals_progress_capability():
    source=(ROOT/'app/main.py').read_text()
    assert 'require_capability(request,db,ctx,"GOALS_PROGRESS")' in source
