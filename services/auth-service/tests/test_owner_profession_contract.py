from pathlib import Path


def test_profession_routes_have_independent_read_write_permissions():
    source = (Path(__file__).parents[1] / "app" / "api" / "v1" / "routes" / "people_access.py").read_text()
    assert '@router.get("/users/{user_id}/profession")' in source
    assert '@router.put("/users/{user_id}/profession")' in source
    assert '"users.read"' in source
    assert '"users.edit"' in source


def test_delegation_is_tenant_scoped_and_audited():
    source = (Path(__file__).parents[1] / "app" / "services" / "owner_profession_service.py").read_text()
    assert 'purpose": "owner_profession_configuration"' in source
    assert '"target_user_id": str(target_user_id)' in source
    assert '"tenant_id": tenant_id' in source
    assert 'OWNER_PROFESSION_UPDATED' in source
    assert 'ambiguous Practice Operations tenant linkage' in source
