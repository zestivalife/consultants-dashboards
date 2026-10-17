from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_p8_migration_is_external_only_and_additive():
    source=(ROOT/'alembic/versions/0009_template_library.py').read_text()
    for table in ('external_template_definitions','external_template_versions','external_template_sections','external_template_items','external_template_audit_events'):assert f'CREATE TABLE {table}' in source
    assert 'ALTER TABLE' not in source

def test_p8_governance_is_versioned_and_system_templates_are_locked():
    source=(ROOT/'app/main.py').read_text()
    for value in ('SYSTEM_TEMPLATE_IMMUTABLE','TEMPLATE_VERSION_CONFLICT','TEMPLATE_OWNER_REQUIRED','VERSION_CREATED','SUPERSEDED'):assert value in source
    for route in ('templates/{template_id}','templates/{template_id}/duplicate','templates/{template_id}/archive'):assert route in source

def test_p8_is_tenant_and_profession_scoped():
    source=(ROOT/'app/main.py').read_text()
    assert "profession_code=:profession" in source
    assert "tenant_id=:tenant" in source

def test_template_collection_routes_precede_generic_resource_routes():
    source=(ROOT/'app/main.py').read_text()
    literal=source.index('@app.get("/api/v1/practice-operations/templates")')
    generic=source.index('@app.get("/api/v1/practice-operations/{resource}")')
    assert literal < generic
    literal_post=source.index('@app.post("/api/v1/practice-operations/templates",status_code=201)')
    generic_post=source.index('@app.post("/api/v1/practice-operations/{resource}", status_code=201)')
    assert literal_post < generic_post
