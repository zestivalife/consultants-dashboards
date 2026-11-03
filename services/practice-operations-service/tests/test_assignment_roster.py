from types import SimpleNamespace

import pytest

from app import assignment_roster
from app.client_directory import client_directory_projection


def _settings():
    return SimpleNamespace(
        external_fiteatsy_outbound_issuer="zestiva",
        external_fiteatsy_outbound_audience="fiteatsy",
        external_fiteatsy_outbound_private_key="test-key",
        external_fiteatsy_outbound_key_id="test-kid",
        external_fiteatsy_backend_url="https://fiteatsy.invalid",
    )


def test_assignment_delegation_is_short_lived_and_purpose_bound(monkeypatch):
    captured = {}
    monkeypatch.setattr(assignment_roster, "get_settings", _settings)
    monkeypatch.setattr(assignment_roster.jwt, "encode", lambda claims, *_args, **_kwargs: captured.update(claims) or "token")

    token = assignment_roster._delegation({
        "user_id": "b1fe3d8e-ebba-4326-9e5a-e18c94e6d055",
        "tenant_id": "2b6b25df-d62f-43dc-a3cf-d6c05bb4b44b",
    })

    assert token == "token"
    assert captured["sub"] == "ext_b1fe3d8e-ebba-4326-9e5a-e18c94e6d055"
    assert captured["permissions"] == ["fiteatsy.external.assignment.read"]
    assert captured["purpose"] == "external_consultant_assignment_roster"
    assert captured["exp"] - captured["iat"] == 60


def test_assignment_projection_exposes_directory_identity_without_health_access():
    projected = client_directory_projection({
        "client_id": "fc_bf838d5a447e1f4180f289b487fc0499",
        "assignment_status": "ACTIVE",
        "assignment_display_name": "Rest fit",
        "assignment_email": "t***@fit.com",
        "assignment_mobile": "******3333",
        "relationship_status": "ASSIGNED_CONNECTION_PENDING",
        "health_data_authorized": False,
        "consented_scopes": [],
    })

    assert projected["name"] == "Rest fit"
    assert projected["email"] == "t***@fit.com"
    assert projected["healthDataAuthorized"] is False
    assert projected["consentedScopes"] == []
    assert projected["relationshipStatus"] == "ASSIGNED_CONNECTION_PENDING"


@pytest.mark.asyncio
async def test_assignment_roster_failure_is_not_converted_to_empty_list(monkeypatch):
    monkeypatch.setattr(assignment_roster, "get_settings", _settings)
    monkeypatch.setattr(assignment_roster, "_delegation", lambda _ctx: "token")

    class Response:
        status_code = 503

    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def get(self, *_args, **_kwargs): return Response()

    monkeypatch.setattr(assignment_roster.httpx, "AsyncClient", lambda **_kwargs: Client())
    with pytest.raises(assignment_roster.AssignmentRosterUnavailable):
        await assignment_roster.list_assigned_fiteatsy_clients({"user_id": "b1fe3d8e-ebba-4326-9e5a-e18c94e6d055", "tenant_id": "tenant"})


@pytest.mark.asyncio
async def test_assignment_roster_is_disabled_when_bridge_is_not_configured(monkeypatch):
    settings = _settings()
    settings.external_fiteatsy_backend_url = None
    monkeypatch.setattr(assignment_roster, "get_settings", lambda: settings)

    assert await assignment_roster.list_assigned_fiteatsy_clients({"user_id": "user", "tenant_id": "tenant"}) == []
