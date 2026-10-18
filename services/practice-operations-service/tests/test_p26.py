from pathlib import Path
from app.p26 import RESOURCE_TYPES,validate_resource_type
ROOT=Path(__file__).parents[1];MIG=(ROOT/'alembic/versions/0026_multi_location.py').read_text();MAIN=(ROOT/'app/main.py').read_text()
def test_one_tenant_multi_location_model():
    assert 'external_practice_locations' in MIG and 'external_location_resource_links' in MIG
    assert 'tenant_id' in MIG and 'tenant_id":ctx["tenant_id"]' in MAIN
    assert 'ONE_TENANT_MULTI_LOCATION' in MAIN
def test_all_required_location_integrations_are_explicit():
    assert RESOURCE_TYPES=={'TEAM_MEMBER','CLIENT','APPOINTMENT','SERVICE','INVOICE','LEAD'}
    for item in RESOURCE_TYPES:assert validate_resource_type(item)==item
    try:validate_resource_type('TENANT');assert False
    except ValueError:pass
