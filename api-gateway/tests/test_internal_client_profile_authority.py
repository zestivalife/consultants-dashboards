import asyncio
import pytest

from app.routers.practice_tenant_resolver import PracticeTenantResolutionError
from app.routers.proxy import INTERNAL_PROFILE_PREFIX, _internal_client_visible


class Response:
    def __init__(self, status_code):
        self.status_code = status_code


class Client:
    def __init__(self, status_code):
        self.status_code = status_code
        self.calls = []

    async def get(self, url, headers):
        self.calls.append((url, headers))
        return Response(self.status_code)


def test_internal_enrichment_authority_reuses_read_only_canonical_workspace_lookup():
    client = Client(200)
    assert asyncio.run(_internal_client_visible(client, "https://fiteatsy.example/", "Bearer token", "client-a"))
    assert client.calls == [("https://fiteatsy.example/v1/consultants/clients/client-a/workspace", {"Authorization":"Bearer token","Accept":"application/json"})]
    assert INTERNAL_PROFILE_PREFIX == "/api/v1/practice-operations/internal-client-profiles"


@pytest.mark.parametrize("status", [403, 404])
def test_internal_enrichment_authority_hides_unauthorised_or_missing_clients(status):
    assert asyncio.run(_internal_client_visible(Client(status), "https://fiteatsy.example", "Bearer token", "client-b")) is False


def test_internal_enrichment_authority_fails_closed_when_source_is_unavailable():
    with pytest.raises(PracticeTenantResolutionError):
        asyncio.run(_internal_client_visible(Client(500), "https://fiteatsy.example", "Bearer token", "client-a"))
