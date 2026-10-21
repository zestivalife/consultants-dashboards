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

def test_privileged_mfa_is_encrypted_replay_protected_and_backend_enforced():
    iam=(ROOT/'app/services/internal_privileged_iam_service.py').read_text()
    auth=(ROOT/'app/services/auth_service.py').read_text()
    people=(ROOT/'app/services/people_access_service.py').read_text()
    assert "Fernet" in iam and "mfa_secret_encrypted" in iam
    assert "MFA code has already been used" in iam
    assert 'user.role.name == "internal_super_admin"' in auth
    assert '"mfa_assured": mfa_assured' in auth
    assert "Recent MFA assurance is required" in people

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
async def test_internal_admin_requires_mfa_and_only_maps_internal_permissions():
    assured=SimpleNamespace(role="internal_super_admin",permissions=["internal.users.read"],mfa_assured=True)
    await ensure_owner_access(None,assured,{"users.read"})
    unassured=SimpleNamespace(role="internal_super_admin",permissions=["internal.users.read"],mfa_assured=False)
    with pytest.raises(ForbiddenException):
        await ensure_owner_access(None,unassured,{"users.read"})
    with pytest.raises(ForbiddenException):
        await ensure_owner_access(None,assured,{"settings.manage"})
