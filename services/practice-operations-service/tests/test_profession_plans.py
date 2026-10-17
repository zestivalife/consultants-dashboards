from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_profession_plan_migration_is_external_only_and_additive():
    source=(ROOT/'alembic/versions/0006_profession_plan_engine.py').read_text()
    for table in ('external_profession_plans','external_profession_plan_versions','external_profession_plan_sections','external_profession_plan_items','external_profession_plan_audit_events'):
        assert f'CREATE TABLE {table}' in source
    assert 'ALTER TABLE' not in source
    assert 'diet_plan' not in source.lower()

def test_profession_plan_lifecycle_and_immutability_are_enforced():
    source=(ROOT/'app/main.py').read_text()
    for route in ('clients/{client_id}/profession-plans','profession-plans/{plan_id}','profession-plans/{plan_id}/publish'):
        assert route in source
    assert 'PUBLISHED_PLAN_IMMUTABLE' in source
    assert "'DRAFT'" in source and "'SAVED'" in source and "'PUBLISHED'" in source
    assert 'PLAN_CAPABILITIES' in source

