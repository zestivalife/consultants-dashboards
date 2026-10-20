from pathlib import Path
from app.p50_audit import PUBLIC_PREFIXES,ROLES,TENANT_DOMAINS,duplicate_routes,migration_chain,route_inventory
ROOT=Path(__file__).parents[1]
def test_routes_have_no_duplicate_method_path():assert duplicate_routes(route_inventory((ROOT/'app/main.py').read_text()))==[]
def test_public_surface_is_explicit_allowlist():
 routes=route_inventory((ROOT/'app/main.py').read_text());public=[path for _,path,name in routes if name.startswith('public_')]
 assert public and all(path.startswith(PUBLIC_PREFIXES) for path in public)
def test_rbac_matrix_is_complete():assert ROLES=={'PLATFORM_OWNER','SUPER_ADMIN','PRACTICE_OWNER','PRACTICE_ADMIN','PRACTITIONER','ASSISTANT','RECEPTIONIST','CLIENT_PORTAL'}
def test_tenant_negative_audit_domains_complete():assert len(TENANT_DOMAINS)==12 and {'support','payouts','subscriptions'}<=TENANT_DOMAINS
def test_migrations_are_one_linear_head():
 chain=migration_chain(ROOT/'alembic/versions');assert chain[0]=='0031_consultant_marketplace' and chain[-1]=='0050_ext_profile_contact_photo' and len(chain)==20
def test_p40_p49_queries_are_bounded_and_tenant_scoped():
 source=(ROOT/'app/main.py').read_text();tail=source[source.index('@app.put("/api/v1/practice-operations/appointments/{appointment_id}/teleconsult'):]
 assert 'LIMIT 100' in tail and 'tenant_id=:tenant' in tail and 'LIMIT 50' in tail
