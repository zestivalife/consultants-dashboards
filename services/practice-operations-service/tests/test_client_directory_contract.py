from datetime import datetime, timezone
from pathlib import Path

from app.client_directory import client_directory_projection


ROOT = Path(__file__).parents[1]


def test_projection_exposes_only_directory_contract_fields():
    now = datetime.now(timezone.utc)
    projected = client_directory_projection({
        "connection_id": "connection-1",
        "client_id": "client-1",
        "state": "ACTIVE",
        "consented_scopes": ["PROFILE", "HEALTH"],
        "connected_at": now,
        "updated_at": now,
        "profile_values": {"firstName": "Asha", "lastName": "Rao", "email": "asha@example.test"},
    })
    assert projected == {
        "id": "client-1", "clientId": "client-1", "connectionId": "connection-1",
        "name": "Asha Rao", "email": "asha@example.test", "mobile": None,
        "status": "ACTIVE", "consentedScopes": ["PROFILE", "HEALTH"],
        "connectedAt": now, "lastActiveAt": now,
    }


def test_directory_route_is_tenant_and_assignment_scoped_and_frontend_uses_it():
    backend = (ROOT / "app/main.py").read_text()
    route = backend[backend.index('@app.get("/api/v1/practice-operations/clients")'):backend.index("async def _team_audit")]
    frontend = (ROOT.parents[1] / "nuetra-frontend/lib/fiteatsyConsultantsApi.js").read_text()
    assert '"CLIENT_LIST_VIEW"' in route
    assert "c.tenant_id=:tenant" in route
    assert "a.user_id=:user" in route
    assert "a.ended_at IS NULL" in route
    assert "external_fiteatsy_connections" in route
    assert "apiRequest(`/practice-operations/clients?${params}`" in frontend
    assert "requestFiteatsy(`/v1/external/clients?${params}`" not in frontend
