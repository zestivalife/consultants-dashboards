from pathlib import Path
from types import SimpleNamespace
import pytest

from app.core.exceptions import ForbiddenException
from app.services.people_access_service import ensure_owner_access

ROOT = Path(__file__).resolve().parents[1]

def test_internal_privileged_role_is_distinct_and_least_privilege():
    migration=(ROOT/'alembic/versions/a4b5c6d7e8f9_internal_privileged_iam.py').read_text()
    assert "internal_super_admin" in migration
    assert "internal.users.manage" in migration
    assert "fiteatsy" not in migration.lower()
    assert "platform_owner'" not in migration
    assert "permissions(id,key,module,label,description" in migration
    assert "category,name" not in migration

def test_interrupted_migration_has_idempotent_repair_revision():
    repair=(ROOT/'alembic/versions/a5b6c7d8e9f0_repair_internal_privileged_iam.py').read_text()
    assert 'down_revision = "a4b5c6d7e8f9"' in repair
    assert "ADD COLUMN IF NOT EXISTS mfa_secret_encrypted" in repair
    assert "CREATE TABLE IF NOT EXISTS internal_privileged_invitations" in repair
    assert "permissions(id,key,module,label,description" in repair

def test_first_admin_bootstrap_migration_is_additive_and_auditable():
    migration=(ROOT/'alembic/versions/b6c7d8e9f0a1_first_internal_admin_bootstrap.py').read_text()
    assert 'down_revision = "a5b6c7d8e9f0"' in migration
    assert "bootstrap_authority_principal" in migration
    assert "bootstrap_grant_hash" in migration
    assert "CREATE UNIQUE INDEX IF NOT EXISTS" in migration
    assert "DROP" not in migration

def test_invitation_is_new_scoped_single_use_two_person_flow():
    source=(ROOT/'app/services/internal_privileged_iam_service.py').read_text()
    assert "InternalPrivilegedInvitation" in source
    assert "hash_token(token)" in source
    assert "Two-person approval is required" in source
    assert "record.token_hash=None" in source
    assert "Identity already exists" in source
    retired=(ROOT/'alembic/versions/f1a2b3c4d5e6_retire_invitation_onboarding_domain.py').read_text()
    assert "user_invitations" in retired
    assert "user_invitations" not in source

def test_legacy_mfa_material_remains_encrypted_but_login_is_password_only():
    iam=(ROOT/'app/services/internal_privileged_iam_service.py').read_text()
    auth=(ROOT/'app/services/auth_service.py').read_text()
    people=(ROOT/'app/services/people_access_service.py').read_text()
    assert "Fernet" in iam and "mfa_secret_encrypted" in iam
    assert "MFA code has already been used" in iam
    assert 'user.role.name == "internal_super_admin"' in auth
    assert '"mfa_assured": mfa_assured' in auth
    assert "verify_totp(user, mfa_code)" not in auth
    assert "Recent MFA assurance is required" not in people

def test_external_authority_sets_do_not_admit_internal_super_admin():
    bridge=(ROOT.parents[1]/'api-gateway/app/routers/fiteatsy_bridge.py').read_text()
    proxy=(ROOT.parents[1]/'api-gateway/app/routers/practice_tenant_resolver.py').read_text()
    assert "internal_super_admin" not in bridge
    assert "internal_super_admin" not in proxy

def test_frontend_hides_external_owner_modules_for_internal_role():
    routes=(ROOT.parents[1]/'nuetra-frontend/lib/ownerConsoleRoutes.js').read_text()
    layout=(ROOT.parents[1]/'nuetra-frontend/components/platform/OwnerConsoleLayout.jsx').read_text()
    page=(ROOT.parents[1]/'nuetra-frontend/components/platform/OwnerConsolePage.jsx').read_text()
    assert "INTERNAL_OWNER_ROUTE_SLUGS" in routes
    assert "marketplace" not in routes.split("INTERNAL_OWNER_ROUTE_SLUGS = new Set(",1)[1].split(");",1)[0]
    assert "internalOnly" in layout
    assert "internalRouteDenied" in page

@pytest.mark.asyncio
async def test_internal_admin_uses_password_session_and_only_maps_internal_permissions():
    unassured=SimpleNamespace(role="internal_super_admin",permissions=["internal.users.read"],mfa_assured=False)
    await ensure_owner_access(None,unassured,{"users.read"})
    with pytest.raises(ForbiddenException):
        await ensure_owner_access(None,unassured,{"settings.manage"})
