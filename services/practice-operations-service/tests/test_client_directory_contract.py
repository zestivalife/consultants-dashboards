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
        "relationship_status": "CONNECTED_CONSENT_ACTIVE",
        "assignment_status": "ACTIVE",
        "health_data_authorized": True,
        "consented_scopes": ["PROFILE", "HEALTH"],
        "connected_at": now,
        "updated_at": now,
        "profile_values": {"firstName": "Asha", "lastName": "Rao", "email": "asha@example.test"},
    })
    assert projected == {
        "id": "client-1", "clientId": "client-1", "connectionId": "connection-1",
        "name": "Asha Rao", "email": "asha@example.test", "mobile": None,
        "status": "CONNECTED_CONSENT_ACTIVE", "relationshipStatus": "CONNECTED_CONSENT_ACTIVE",
        "assignmentStatus": "ACTIVE", "connectionState": "ACTIVE", "healthDataAuthorized": True,
        "consentedScopes": ["PROFILE", "HEALTH"],
        "connectedAt": now, "lastActiveAt": now,
    }


def test_assigned_unconnected_client_is_visible_without_health_data_authority():
    projected = client_directory_projection({
        "connection_id": None,
        "client_id": "client-pending",
        "state": None,
        "relationship_status": "ASSIGNED_CONNECTION_PENDING",
        "assignment_status": "ACTIVE",
        "health_data_authorized": False,
        "consented_scopes": None,
        "connected_at": None,
        "updated_at": None,
        "profile_values": {"name": "Pending Client"},
    })
    assert projected["connectionId"] is None
    assert projected["name"] == "Unnamed client"
    assert projected["email"] is None
    assert projected["relationshipStatus"] == "ASSIGNED_CONNECTION_PENDING"
    assert projected["healthDataAuthorized"] is False
    assert projected["consentedScopes"] == []


def test_revoked_connection_remains_a_restricted_directory_state():
    projected = client_directory_projection({
        "connection_id": "connection-revoked",
        "client_id": "client-revoked",
        "state": "REVOKED",
        "relationship_status": "CONSENT_REVOKED",
        "assignment_status": "ACTIVE",
        "health_data_authorized": False,
        "consented_scopes": ["DIET_PLANS"],
        "connected_at": None,
        "updated_at": None,
        "profile_values": {},
    })
    assert projected["connectionState"] == "REVOKED"
    assert projected["relationshipStatus"] == "CONSENT_REVOKED"
    assert projected["healthDataAuthorized"] is False


def test_connected_directory_name_requires_active_profile_consent():
    row = {
        "connection_id": "connection-directory",
        "client_id": "canonical-client",
        "state": "ACTIVE",
        "relationship_status": "CONNECTED_CONSENT_ACTIVE",
        "assignment_status": "NONE",
        "health_data_authorized": True,
        "consented_scopes": ["PROFILE", "DIET_PLANS"],
        "directory_display_name": "QA Connected Client",
        "profile_values": {},
    }
    connected = client_directory_projection(row)
    restricted = client_directory_projection({
        **row,
        "health_data_authorized": False,
        "consented_scopes": ["DIET_PLANS"],
    })
    assert connected["name"] == "QA Connected Client"
    assert restricted["name"] == "Unnamed client"


def test_directory_route_is_tenant_and_assignment_scoped_and_frontend_uses_it():
    backend = (ROOT / "app/main.py").read_text()
    route = backend[backend.index('@app.get("/api/v1/practice-operations/clients")'):backend.index("async def _team_audit")]
    frontend = (ROOT.parents[1] / "nuetra-frontend/lib/fiteatsyConsultantsApi.js").read_text()
    assert '"CLIENT_LIST_VIEW"' in route
    assert "a.tenant_id=:tenant" in route
    assert "ASSIGNED_CONNECTION_PENDING" in route
    assert "CONSENT_REVOKED" in route
    assert "(c.state='ACTIVE') health_data_authorized" in route
    assert "a.user_id=:user" in route
    assert "a.ended_at IS NULL" in route
    assert "external_fiteatsy_connections" in route
    assert "fiteatsy_client_directory" in route
    assert "COALESCE(c.consultant_client_id,fd.fiteatsy_client_id)" in route
    assert "fd.deleted_at IS NULL AND fd.sync_status='CURRENT'" in route
    assert "apiRequest(`/practice-operations/clients?${params}`" in frontend
    assert "requestFiteatsy(`/v1/external/clients?${params}`" not in frontend
