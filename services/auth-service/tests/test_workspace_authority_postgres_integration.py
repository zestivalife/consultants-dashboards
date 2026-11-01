import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import asyncpg
import httpx
import pytest


INTEGRATION_DATABASE_URL = os.getenv("AUTH_INTEGRATION_DATABASE_URL")
pytestmark = pytest.mark.skipif(not INTEGRATION_DATABASE_URL, reason="isolated Auth PostgreSQL integration database is required")


async def seed_identities() -> dict[str, str]:
    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    now = datetime.now(timezone.utc)
    identities: dict[str, str] = {}
    try:
        await connection.execute("TRUNCATE external_signup_provisioning, external_signup_challenges, organization_memberships, organizations RESTART IDENTITY CASCADE")
        await connection.execute("DELETE FROM users WHERE email LIKE '%@qa.invalid'")
        role_rows = await connection.fetch("SELECT id::text,name FROM roles WHERE name IN ('consultant','senior_consultant','superuser')")
        roles = {row["name"]: row["id"] for row in role_rows}
        for key, role in (("internal", "consultant"), ("external", "consultant"), ("senior", "senior_consultant"), ("super", "superuser"), ("inactive", "consultant")):
            user_id = str(uuid4());identities[key] = user_id
            await connection.execute("""INSERT INTO users
              (id,email,password_hash,role_id,is_verified,failed_login_attempts,created_at,updated_at,is_active,
               permissions,status,email_verified,mobile_verified,remember_me,mfa_enabled,current_session_version,
               refresh_token_version,must_change_password,credential_status,account_classification)
              VALUES($1,$2,'fixture',$3,TRUE,0,$4,$4,TRUE,'[]','ACTIVE',TRUE,FALSE,FALSE,FALSE,0,0,FALSE,'PERMANENT','PRODUCTION_USER')""",
              user_id, f"{key}@qa.invalid", roles[role], now)
        organizations = []
        for name in ("Internal QA One", "Internal QA Two"):
            organization_id = str(uuid4());organizations.append(organization_id)
            await connection.execute("""INSERT INTO organizations(id,name,status,created_at,updated_at)
              VALUES($1,$2,'ACTIVE',$3,$3)""", organization_id, name, now)
        for user_key, organization_id, status in (
            ("internal", organizations[0], "ACTIVE"),
            ("senior", organizations[0], "ACTIVE"),
            ("senior", organizations[1], "ACTIVE"),
            ("inactive", organizations[0], "INACTIVE"),
        ):
            await connection.execute("""INSERT INTO organization_memberships
              (id,user_id,organization_id,status,is_verified,tags,joined_at,created_at,updated_at)
              VALUES($1,$2,$3,$4,TRUE,'[]',$5,$5,$5)""", uuid4(), identities[user_key], organization_id, status, now)
        challenge_id = str(uuid4())
        await connection.execute("""INSERT INTO external_signup_challenges
          (id,email_normalized,otp_hash,status,attempt_count,resend_count,expires_at,last_sent_at,consumed_at,created_at,updated_at)
          VALUES($1,'external@qa.invalid','fixture','CONSUMED',0,0,$2,$3,$3,$3,$3)""", challenge_id, now + timedelta(hours=1), now)
        await connection.execute("""INSERT INTO external_signup_provisioning
          (id,challenge_id,auth_user_id,account_type,idempotency_key,status,fiteatsy_user_id,tenant_id,owner_membership_id,created_at,updated_at)
          VALUES($1,$2,$3,'INDEPENDENT_CONSULTANT',$4,'READY','mobile-external','external-tenant','external-owner',$5,$5)""",
          uuid4(), challenge_id, identities["external"], str(uuid4()), now)
    finally:
        await connection.close()
    return identities


@pytest.mark.asyncio
async def test_auth_me_projects_only_persisted_role_and_membership_authority():
    identities = await seed_identities()
    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        responses = {key: await client.get("/api/v1/auth/me", headers={"X-User-Id": user_id}) for key, user_id in identities.items()}
    assert all(response.status_code == 200 for response in responses.values()), {key: (response.status_code, response.text) for key, response in responses.items()}
    data = {key: response.json()["data"] for key, response in responses.items()}

    internal = data["internal"]["workspaceAuthorities"]
    assert [(item["workspaceId"], item["tenantType"], item["resolutionPath"]) for item in internal] == [("internal-consultant", "ZESTIVA_INTERNAL", "MEMBERSHIP")]
    assert data["internal"]["currentTenant"]["tenantId"] == internal[0]["tenantId"]

    external = data["external"]["workspaceAuthorities"]
    assert len(external) == 1
    assert external[0]["workspaceId"] == "external-consultant"
    assert external[0]["tenantId"] == "external-tenant"
    assert external[0]["resolutionPath"] == "MEMBERSHIP"
    assert data["external"]["currentTenant"]["tenantType"] == "INDEPENDENT_CONSULTANT"

    senior = data["senior"]["workspaceAuthorities"]
    assert len(senior) == 2
    assert {item["workspaceId"] for item in senior} == {"senior-consultant"}
    assert len({item["tenantId"] for item in senior}) == 2

    super_authority = data["super"]["workspaceAuthorities"]
    assert len(super_authority) == 1
    assert super_authority[0]["workspaceId"] == "super-admin"
    assert super_authority[0]["resolutionPath"] == "BACKEND_ROLE"
    assert super_authority[0].get("tenantId") is None

    assert data["inactive"]["workspaceAuthorities"] == []
    assert data["inactive"]["currentTenant"] is None
