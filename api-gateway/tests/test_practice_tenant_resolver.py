import asyncio

import pytest

from app.routers.practice_tenant_resolver import (
    PracticeTenantResolutionError,
    client_belongs_to_authenticated_tenant,
    is_practice_operations_path,
    is_platform_marketplace_admin_path,
    is_platform_owner_directory_path,
    is_platform_owner_role,
    parse_practice_tenant_authority,
    practice_client_resource_id,
    resolve_practice_tenant_authority,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get(self, url, headers):
        self.calls.append((url, headers))
        if isinstance(self.response, list):
            return self.response[len(self.calls) - 1]
        return self.response


def tenant_payload(**overrides):
    tenant = {
        "tenantId": "external-tenant-1",
        "tenantType": "INDEPENDENT_CONSULTANT",
        "currentMembershipRole": "OWNER",
        "resolutionPath": "MEMBERSHIP",
        "membershipStatus": "ACTIVE",
        "tenantStatus": "ACTIVE",
    }
    tenant.update(overrides)
    return {"currentTenant": tenant}


@pytest.mark.parametrize("tenant_type", ["INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"])
def test_accepts_active_external_membership_types(tenant_type):
    authority = parse_practice_tenant_authority(tenant_payload(tenantType=tenant_type))
    assert authority.tenant_id == "external-tenant-1"
    assert authority.tenant_type == tenant_type
    assert authority.membership_role == "OWNER"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        tenant_payload(membershipStatus="INACTIVE"),
        tenant_payload(tenantStatus="INACTIVE"),
        tenant_payload(tenantType="ZESTIVA_INTERNAL"),
        tenant_payload(resolutionPath="CLIENT_SELECTED"),
        tenant_payload(tenantId=""),
    ],
)
def test_fails_closed_for_missing_inactive_internal_or_untrusted_authority(payload):
    with pytest.raises(PracticeTenantResolutionError):
        parse_practice_tenant_authority(payload)


def test_resolver_uses_only_bearer_authenticated_server_context():
    # Exercise the real response shape used by the frontend contract.
    client = FakeClient(FakeResponse(payload={"data": tenant_payload()}))
    authority = asyncio.run(
        resolve_practice_tenant_authority(
            client,
            auth_service_url="https://auth.example/",
            fiteatsy_service_url="https://fiteatsy.example/",
            authorization="Bearer signed-token",
            authenticated_user_id="user-1",
        )
    )
    assert authority.tenant_id == "external-tenant-1"
    assert authority.profession_hint is None
    assert client.calls == [
        (
            "https://auth.example/api/v1/auth/me",
            {"Authorization": "Bearer signed-token", "Accept": "application/json"},
        ),
    ]


def test_resolver_does_not_forward_zestiva_token_to_legacy_fiteatsy_onboarding():
    explicit = FakeClient(FakeResponse(payload=tenant_payload()))
    authority = asyncio.run(resolve_practice_tenant_authority(
        explicit,
        auth_service_url="https://auth.example",
        fiteatsy_service_url="https://fiteatsy.example",
        authorization="Bearer signed-token",
        authenticated_user_id="user-1",
    ))
    assert authority.profession_hint is None
    assert [call[0] for call in explicit.calls] == ["https://auth.example/api/v1/auth/me"]


def test_resolver_denies_no_membership_and_missing_identity():
    no_membership = FakeClient(FakeResponse(status_code=403, payload={}))
    with pytest.raises(PracticeTenantResolutionError):
        asyncio.run(
            resolve_practice_tenant_authority(
                no_membership,
                auth_service_url="https://auth.example",
                fiteatsy_service_url="https://fiteatsy.example",
                authorization="Bearer signed-token",
                authenticated_user_id="user-1",
            )
        )
    with pytest.raises(PracticeTenantResolutionError):
        asyncio.run(
            resolve_practice_tenant_authority(
                no_membership,
                auth_service_url="https://auth.example",
                fiteatsy_service_url="https://fiteatsy.example",
                authorization=None,
                authenticated_user_id="user-1",
            )
        )


def test_scope_is_exactly_practice_operations_namespace():
    assert is_practice_operations_path("/api/v1/practice-operations")
    assert is_practice_operations_path("/api/v1/practice-operations/tasks")
    assert not is_practice_operations_path("/api/v1/auth/me")
    assert not is_practice_operations_path("/api/v1/profile")
    assert not is_practice_operations_path("/api/v1/practice-operations-internal")


def test_only_platform_marketplace_admin_namespace_bypasses_tenant_resolution():
    assert is_platform_marketplace_admin_path("/api/v1/practice-operations/admin/marketplace")
    assert is_platform_marketplace_admin_path("/api/v1/practice-operations/admin/marketplace/finance")
    assert not is_platform_marketplace_admin_path("/api/v1/practice-operations/marketplace/profile")
    assert not is_platform_marketplace_admin_path("/api/v1/practice-operations/admin/other")


def test_only_exact_platform_owner_directory_path_bypasses_external_tenant_resolution():
    path = "/api/v1/practice-operations/fiteatsy-client-directory"
    assert is_platform_owner_directory_path(path)
    assert not is_platform_owner_directory_path(path + "/client-a")
    assert not is_platform_owner_directory_path("/api/v1/practice-operations/clients")


def test_platform_owner_directory_roles_are_explicit_and_fail_closed():
    for role in ("platform_owner", "SUPERUSER", "super_admin"):
        assert is_platform_owner_role(role)
    for role in (None, "", "consultant", "senior_consultant", "admin", "member"):
        assert not is_platform_owner_role(role)


def test_only_direct_client_resource_paths_are_class_b():
    assert practice_client_resource_id("/api/v1/practice-operations/clients/client-a/progress") == "client-a"
    assert practice_client_resource_id("/api/v1/practice-operations/tasks") is None
    assert practice_client_resource_id("/api/v1/practice-operations/clients") is None


def test_client_authority_uses_one_tenant_scoped_lookup_without_existence_probe():
    visible = FakeClient(FakeResponse(status_code=200, payload={}))
    assert asyncio.run(client_belongs_to_authenticated_tenant(
        visible,
        fiteatsy_service_url="https://fiteatsy.example",
        authorization="Bearer signed-token",
        client_id="client-a",
    ))
    assert len(visible.calls) == 1

    foreign = FakeClient(FakeResponse(status_code=404, payload={}))
    assert not asyncio.run(client_belongs_to_authenticated_tenant(
        foreign,
        fiteatsy_service_url="https://fiteatsy.example",
        authorization="Bearer signed-token",
        client_id="client-b",
    ))
    assert len(foreign.calls) == 1
