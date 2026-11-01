import asyncio

import pytest

from app.routers.practice_tenant_resolver import (
    PracticeTenantAuthorityUnavailable,
    PracticeTenantResolutionError,
    is_practice_operations_path,
    is_platform_marketplace_admin_path,
    parse_practice_tenant_authority,
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


def multi_tenant_payload():
    return {"workspaceAuthorities": [
        {**tenant_payload()["currentTenant"], "workspaceId": "external-consultant"},
        {**tenant_payload(tenantId="external-tenant-2", tenantType="PRACTICE")["currentTenant"], "workspaceId": "external-consultant"},
    ]}


@pytest.mark.parametrize("tenant_type", ["INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"])
def test_accepts_active_external_membership_types(tenant_type):
    authority = parse_practice_tenant_authority(tenant_payload(tenantType=tenant_type))
    assert authority.tenant_id == "external-tenant-1"
    assert authority.tenant_type == tenant_type
    assert authority.membership_role == "OWNER"


def test_accepts_real_auth_workspace_authority_role_contract():
    payload = {
        "data": {
            "workspaceAuthorities": [
                {
                    "workspaceId": "external-consultant",
                    "tenantId": "external-tenant-1",
                    "tenantType": "PRACTICE",
                    "role": "consultant",
                    "membershipStatus": "active",
                    "resolutionPath": "MEMBERSHIP",
                }
            ]
        }
    }

    authority = parse_practice_tenant_authority(payload)

    assert authority.tenant_id == "external-tenant-1"
    assert authority.membership_role == "CONSULTANT"


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
    client = FakeClient([
        FakeResponse(payload={"data": tenant_payload()}),
        FakeResponse(payload={"onboarding": {"professionalTitle": "DIETITIAN_NUTRITIONIST"}}),
    ])
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
    assert authority.profession_hint == "DIETITIAN_NUTRITIONIST"
    assert client.calls == [
        (
            "https://auth.example/api/v1/auth/me",
            {"Authorization": "Bearer signed-token", "Accept": "application/json"},
        ),
        (
            "https://fiteatsy.example/v1/consultants/onboarding",
            {"Authorization": "Bearer signed-token", "Accept": "application/json"},
        ),
    ]


def test_resolver_prefers_explicit_onboarding_profession_and_fails_safe_when_unavailable():
    explicit = FakeClient([
        FakeResponse(payload=tenant_payload()),
        FakeResponse(payload={"onboarding": {
            "professionalTitle": "Other healthcare professional",
            "professionalDetails": {"profession": "Clinical Nutritionist"},
        }}),
    ])
    authority = asyncio.run(resolve_practice_tenant_authority(
        explicit,
        auth_service_url="https://auth.example",
        fiteatsy_service_url="https://fiteatsy.example",
        authorization="Bearer signed-token",
        authenticated_user_id="user-1",
    ))
    assert authority.profession_hint == "Clinical Nutritionist"

    unavailable = FakeClient([
        FakeResponse(payload=tenant_payload()),
        FakeResponse(status_code=404, payload={}),
    ])
    authority = asyncio.run(resolve_practice_tenant_authority(
        unavailable,
        auth_service_url="https://auth.example",
        fiteatsy_service_url="https://fiteatsy.example",
        authorization="Bearer signed-token",
        authenticated_user_id="user-1",
    ))
    assert authority.profession_hint is None


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


def test_multi_tenant_authority_requires_and_validates_explicit_selection():
    with pytest.raises(PracticeTenantResolutionError, match="selection"):
        parse_practice_tenant_authority(multi_tenant_payload())
    selected = parse_practice_tenant_authority(multi_tenant_payload(), "external-tenant-2")
    assert selected.tenant_id == "external-tenant-2"
    assert selected.tenant_type == "PRACTICE"
    with pytest.raises(PracticeTenantResolutionError, match="No active"):
        parse_practice_tenant_authority(multi_tenant_payload(), "foreign-tenant")


def test_membership_authority_outage_is_not_misclassified_as_missing_membership():
    unavailable = FakeClient(FakeResponse(status_code=503, payload={}))
    with pytest.raises(PracticeTenantAuthorityUnavailable):
        asyncio.run(resolve_practice_tenant_authority(
            unavailable,
            auth_service_url="https://auth.example",
            fiteatsy_service_url="https://fiteatsy.example",
            authorization="Bearer signed-token",
            authenticated_user_id="user-1",
        ))


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
