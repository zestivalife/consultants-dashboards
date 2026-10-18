from pathlib import Path

ROOT=Path(__file__).parents[1]
MAIN=(ROOT/'app/main.py').read_text()
MIGRATION=(ROOT/'alembic/versions/0021_form_builder.py').read_text()

def test_p21_external_only_schema_and_immutable_versions():
    for table in ('external_form_definitions','external_form_versions','external_form_sections','external_form_fields','external_form_assignments','external_form_responses','external_form_audit_events'):
        assert f'CREATE TABLE {table}' in MIGRATION
    assert '0020_progress_reports' in MIGRATION
    assert 'SUPERSEDED' in MAIN and 'FORM_RESPONSE_IMMUTABLE' in MAIN

def test_p21_governed_routes_are_tenant_scoped():
    for route in ('/forms','/forms/{form_id}/publish','/forms/{form_id}/assign','/form-assignments','/form-assignments/{assignment_id}/response'):
        assert route in MAIN
    assert 'AND tenant_id=:tenant' in MAIN
    assert 'PUBLISHED_FORM_NOT_FOUND' in MAIN

def test_p21_declarative_fields_no_code_execution():
    contracts=(ROOT/'app/contracts.py').read_text()
    for field in ('SHORT_TEXT','REPEAT_GROUP','CONSENT_CHECKBOX','BODY_REGION'):
        assert field in contracts
    assert 'condition: dict[str,Any] | None' in contracts
    assert 'eval(' not in MAIN and 'exec(' not in MAIN
