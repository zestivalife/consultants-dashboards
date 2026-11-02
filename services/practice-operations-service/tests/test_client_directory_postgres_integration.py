import os
from datetime import datetime, timezone
from uuid import uuid4

import asyncpg
import httpx
import pytest
import pytest_asyncio


INTEGRATION_DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")
pytestmark = pytest.mark.skipif(not INTEGRATION_DATABASE_URL, reason="isolated PostgreSQL integration database is required")


@pytest_asyncio.fixture(autouse=True)
async def isolated_application_pool():
    import app.db as database
    if database._engine is not None:
        await database._engine.dispose()
    database._engine = None
    database._factory = None
    yield
    if database._engine is not None:
        await database._engine.dispose()
    database._engine = None
    database._factory = None


def headers(user: str, tenant: str = "tenant-a", tenant_type: str = "PRACTICE") -> dict[str, str]:
    return {"X-User-Id": user, "X-Tenant-Id": tenant, "X-Tenant-Type": tenant_type, "X-User-Role": "CONSULTANT"}


async def seed_directory() -> None:
    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    now = datetime.now(timezone.utc)
    try:
        await connection.execute("TRUNCATE external_client_profile_enrichments, external_fiteatsy_connections, external_client_team_assignments, external_practice_role_profiles, practice_tenant_configuration, fiteatsy_client_directory CASCADE")
        for tenant in ("tenant-a", "tenant-b"):
            await connection.execute("""INSERT INTO practice_tenant_configuration
              (tenant_id,profession,capabilities,terminology,profile,version,updated_by,updated_at)
              VALUES($1,'NUTRITIONIST','[\"CLIENT_CRM\",\"DIET_PLAN\"]','{}','{}',1,'fixture',$2)""", tenant, now)
        roles = [
            ("tenant-a", "consultant-a", "PRACTITIONER", "ACTIVE", False),
            ("tenant-a", "consultant-other", "PRACTITIONER", "ACTIVE", False),
            ("tenant-a", "consultant-suspended", "PRACTITIONER", "SUSPENDED", False),
            ("tenant-a", "practice-owner", "PRACTICE_OWNER", "ACTIVE", True),
        ]
        for tenant, user, role, status, wide in roles:
            await connection.execute("""INSERT INTO external_practice_role_profiles
              (id,tenant_id,user_id,role,status,profession_code,permission_grants,permission_restrictions,
               practice_wide_client_access,active_from,created_by,created_at,updated_at)
              VALUES($1,$2,$3,$4,$5,$6,'[]','[]',$7,$8,'fixture',$8,$8)""",
              uuid4(), tenant, user, role, status, "NUTRITIONIST" if role == "PRACTITIONER" else None, wide, now)

        assignments = [
            ("tenant-a", "client-pending", "consultant-a", "PRIMARY_PRACTITIONER", None),
            ("tenant-a", "client-connected", "consultant-a", "PRIMARY_PRACTITIONER", None),
            ("tenant-a", "client-revoked", "consultant-a", "PRIMARY_PRACTITIONER", None),
            ("tenant-a", "client-inactive", "consultant-a", "PRIMARY_PRACTITIONER", None),
            ("tenant-a", "client-duplicate", "consultant-a", "PRIMARY_PRACTITIONER", None),
            ("tenant-a", "client-duplicate", "consultant-a", "CARE_TEAM_MEMBER", None),
            ("tenant-a", "client-other", "consultant-other", "PRIMARY_PRACTITIONER", None),
            ("tenant-a", "client-removed", "consultant-a", "PRIMARY_PRACTITIONER", now),
            ("tenant-b", "client-cross-tenant", "consultant-a", "PRIMARY_PRACTITIONER", None),
        ]
        for tenant, client, user, role, ended in assignments:
            await connection.execute("""INSERT INTO external_client_team_assignments
              (id,tenant_id,client_id,user_id,assignment_role,assigned_by,assigned_at,ended_at)
              VALUES($1,$2,$3,$4,$5,'fixture',$6,$7)""", uuid4(), tenant, client, user, role, now, ended)

        connections = [
            ("tenant-a", "consultant-a", "client-connected", "ACTIVE"),
            ("tenant-a", "consultant-a", "client-revoked", "REVOKED"),
            ("tenant-a", "consultant-a", "client-inactive", "SUSPENDED"),
            ("tenant-a", "consultant-a", "client-duplicate", "ACTIVE"),
            ("tenant-a", "consultant-a", "client-unassigned", "ACTIVE"),
            ("tenant-a", "consultant-a", "client-removed", "ACTIVE"),
            ("tenant-a", "consultant-other", "client-other", "ACTIVE"),
            ("tenant-b", "consultant-a", "client-cross-tenant", "ACTIVE"),
        ]
        for tenant, consultant, client, state in connections:
            await connection.execute("""INSERT INTO external_fiteatsy_connections
              (id,tenant_id,consultant_id,fiteatsy_user_id,consultant_client_id,state,consent_version,
               consented_scopes,programme_status,connected_at,disconnected_at,updated_at)
              VALUES($1,$2,$3,$4,$5,$6,'v1','[\"PROFILE\",\"DIET_PLANS\"]','ACTIVE',$7,$8,$7)""",
              uuid4(), tenant, consultant, f"mobile-{tenant}-{client}", client, state, now, now if state != "ACTIVE" else None)
        directory_user_id = uuid4()
        await connection.execute("""INSERT INTO fiteatsy_client_directory
          (id,fiteatsy_user_id,fiteatsy_client_id,display_name,account_status,mobile_verified,
           registration_status,registered_at,source_updated_at,source_version,last_synced_at,sync_status,
           created_at,updated_at)
          VALUES($1,$2,'client-directory-linked','QA Directory Linked','ACTIVE',TRUE,'COMPLETED',$3,$3,1,$3,'CURRENT',$3,$3)""",
          uuid4(), directory_user_id, now)
        await connection.execute("""INSERT INTO external_fiteatsy_connections
          (id,tenant_id,consultant_id,fiteatsy_user_id,consultant_client_id,state,consent_version,
           consented_scopes,programme_status,connected_at,updated_at)
          VALUES($1,'tenant-a','practice-owner',$2,NULL,'ACTIVE','v1','["PROFILE","DIET_PLANS"]','ACTIVE',$3,$3)""",
          uuid4(), str(directory_user_id), now)
        for tenant, client in (("tenant-a", value) for value in {row[1] for row in assignments if row[0] == "tenant-a"} | {"client-unassigned"}):
            await connection.execute("""INSERT INTO external_client_profile_enrichments
              (tenant_id,client_id,values,version,schema_version,provenance,audit_history,created_by,updated_by,created_at,updated_at)
              VALUES($1,$2,CAST($3 AS jsonb),1,1,'{}','[]','fixture','fixture',$4,$4)""",
              tenant, client, f'{{"name":"Profile {client}","email":"{client}@example.test"}}', now)
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_real_http_client_directory_assignment_consent_pagination_and_isolation():
    await seed_directory()
    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        unauthenticated = await client.get("/api/v1/practice-operations/clients")
        assert unauthenticated.status_code == 401
        wrong_scope = await client.get("/api/v1/practice-operations/clients", headers=headers("consultant-a", tenant_type="ZESTIVA_INTERNAL"))
        assert wrong_scope.status_code == 403
        suspended = await client.get("/api/v1/practice-operations/clients", headers=headers("consultant-suspended"))
        assert suspended.status_code == 403

        first = await client.get("/api/v1/practice-operations/clients?limit=2&offset=0", headers=headers("consultant-a"))
        second = await client.get("/api/v1/practice-operations/clients?limit=2&offset=2", headers=headers("consultant-a"))
        tail = await client.get("/api/v1/practice-operations/clients?limit=2&offset=4", headers=headers("consultant-a"))
        assert first.status_code == second.status_code == tail.status_code == 200
        pages = [first.json()["data"], second.json()["data"], tail.json()["data"]]
        assert all(page["pagination"]["total"] == 5 for page in pages)
        rows = [row for page in pages for row in page["clients"]]
        assert len(rows) == len({row["clientId"] for row in rows}) == 5
        by_id = {row["clientId"]: row for row in rows}
        assert set(by_id) == {"client-pending", "client-connected", "client-revoked", "client-inactive", "client-duplicate"}
        assert by_id["client-pending"]["relationshipStatus"] == "ASSIGNED_CONNECTION_PENDING"
        assert by_id["client-pending"]["healthDataAuthorized"] is False
        assert by_id["client-pending"]["email"] is None
        assert by_id["client-connected"]["relationshipStatus"] == "CONNECTED_CONSENT_ACTIVE"
        assert by_id["client-connected"]["healthDataAuthorized"] is True
        assert by_id["client-revoked"]["relationshipStatus"] == "CONSENT_REVOKED"
        assert by_id["client-revoked"]["healthDataAuthorized"] is False
        assert by_id["client-inactive"]["relationshipStatus"] == "CONSENT_INACTIVE"

        filtered = await client.get("/api/v1/practice-operations/clients?status=CONSENT_REVOKED", headers=headers("consultant-a"))
        assert filtered.status_code == 200
        assert [row["clientId"] for row in filtered.json()["data"]["clients"]] == ["client-revoked"]

        wide = await client.get("/api/v1/practice-operations/clients?limit=100", headers=headers("practice-owner"))
        assert wide.status_code == 200
        wide_ids = [row["clientId"] for row in wide.json()["data"]["clients"]]
        assert wide.json()["data"]["practiceWide"] is True
        assert len(wide_ids) == len(set(wide_ids))
        assert {"client-unassigned", "client-other", "client-removed", "client-directory-linked"}.issubset(wide_ids)
        linked = next(row for row in wide.json()["data"]["clients"] if row["clientId"] == "client-directory-linked")
        assert linked["name"] == "QA Directory Linked"
        assert linked["relationshipStatus"] == "CONNECTED_CONSENT_ACTIVE"
        assert linked["assignmentStatus"] == "NONE"
        assert linked["healthDataAuthorized"] is True
        assert "client-cross-tenant" not in wide_ids
