import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
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


@pytest.mark.asyncio
async def test_invited_consultants_activate_membership_during_temporary_password_journey(monkeypatch):
    from app.services.password_service import password_service
    from app.services import auth_service

    monkeypatch.setattr(auth_service, "check_rate_limit", AsyncMock(return_value=True))

    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    now = datetime.now(timezone.utc)
    temporary_password = "Temporary!Passphrase2026"
    replacement_password = "Replacement!Passphrase2026"
    identities = []
    try:
        await connection.execute("TRUNCATE external_signup_provisioning, external_signup_challenges, organization_memberships, organizations RESTART IDENTITY CASCADE")
        await connection.execute("DELETE FROM users WHERE email LIKE 'qa+%-journey@zestiva.test'")
        roles = {row["name"]: row["id"] for row in await connection.fetch("SELECT id::text,name FROM roles WHERE name IN ('consultant','senior_consultant')")}
        organization_id = str(uuid4())
        await connection.execute("INSERT INTO organizations(id,name,status,created_at,updated_at) VALUES($1,'Provisioning Journey QA','ACTIVE',$2,$2)", organization_id, now)
        for label, role in (("internal", "consultant"), ("senior", "senior_consultant")):
            user_id = str(uuid4())
            email = f"qa+{label}-journey@zestiva.test"
            identities.append((label, user_id, email))
            await connection.execute("""INSERT INTO users
              (id,email,password_hash,role_id,is_verified,failed_login_attempts,created_at,updated_at,is_active,
               permissions,status,email_verified,mobile_verified,remember_me,mfa_enabled,current_session_version,
               refresh_token_version,must_change_password,credential_status,temporary_password_created_at,
               temporary_password_expires_at,account_classification)
              VALUES($1,$2,$3,$4,TRUE,0,$5,$5,TRUE,'[]','INVITED',TRUE,FALSE,FALSE,FALSE,0,0,TRUE,
                     'TEMPORARY',$5,$6,'PRODUCTION_USER')""",
              user_id, email, password_service.hash_password(temporary_password), roles[role], now, now + timedelta(days=1))
            await connection.execute("""INSERT INTO organization_memberships
              (id,user_id,organization_id,status,is_verified,tags,joined_at,created_at,updated_at)
              VALUES($1,$2,$3,'INVITED',TRUE,'[]',$4,$4,$4)""", uuid4(), user_id, organization_id, now)
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_temporary_password_change_rejects_ambiguous_invited_memberships(monkeypatch):
    from app.services.password_service import password_service
    from app.services import auth_service

    monkeypatch.setattr(auth_service, "check_rate_limit", AsyncMock(return_value=True))
    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    now = datetime.now(timezone.utc)
    temporary_password = "Temporary!Ambiguous2026"
    replacement_password = "Replacement!Ambiguous2026"
    email = "qa+ambiguous-memberships@zestiva.test"
    user_id = str(uuid4())
    try:
        await connection.execute("DELETE FROM users WHERE email = $1", email)
        role_id = await connection.fetchval("SELECT id::text FROM roles WHERE name = 'consultant'")
        await connection.execute(
            """INSERT INTO users
            (id,email,password_hash,role_id,is_verified,failed_login_attempts,created_at,updated_at,is_active,
             permissions,status,email_verified,mobile_verified,remember_me,mfa_enabled,current_session_version,
             refresh_token_version,must_change_password,credential_status,temporary_password_created_at,
             temporary_password_expires_at,account_classification)
            VALUES($1,$2,$3,$4,TRUE,0,$5,$5,TRUE,'[]','INVITED',TRUE,FALSE,FALSE,FALSE,0,0,TRUE,
                   'TEMPORARY',$5,$6,'PRODUCTION_USER')""",
            user_id,
            email,
            password_service.hash_password(temporary_password),
            role_id,
            now,
            now + timedelta(days=1),
        )
        for index in range(2):
            organization_id = str(uuid4())
            await connection.execute(
                "INSERT INTO organizations(id,name,status,created_at,updated_at) VALUES($1,$2,'ACTIVE',$3,$3)",
                organization_id,
                f"Ambiguous Membership QA {index}",
                now,
            )
            await connection.execute(
                """INSERT INTO organization_memberships
                (id,user_id,organization_id,status,is_verified,tags,joined_at,created_at,updated_at)
                VALUES($1,$2,$3,'INVITED',TRUE,'[]',$4,$4,$4)""",
                uuid4(),
                user_id,
                organization_id,
                now,
            )
    finally:
        await connection.close()

    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": temporary_password})
        assert login.status_code == 200, login.text
        changed = await client.post(
            "/api/v1/auth/change-temporary-password",
            headers={"Authorization": f"Bearer {login.json()['data']['tokens']['access_token']}"},
            json={
                "current_password": temporary_password,
                "new_password": replacement_password,
                "confirm_password": replacement_password,
            },
        )
        assert changed.status_code == 409, changed.text
        assert "administrator resolution" in changed.json()["message"]

    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    try:
        states = await connection.fetch(
            "SELECT status FROM organization_memberships WHERE user_id = $1 ORDER BY organization_id",
            user_id,
        )
        assert [row["status"] for row in states] == ["INVITED", "INVITED"]
        user_state = await connection.fetchrow(
            "SELECT must_change_password, credential_status FROM users WHERE id = $1", user_id
        )
        assert user_state["must_change_password"] is True
        assert user_state["credential_status"] == "TEMPORARY"
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_temporary_password_change_does_not_activate_unrelated_memberships(monkeypatch):
    from app.services.password_service import password_service
    from app.services import auth_service

    monkeypatch.setattr(auth_service, "check_rate_limit", AsyncMock(return_value=True))
    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    now = datetime.now(timezone.utc)
    temporary_password = "Temporary!Existing2026"
    replacement_password = "Replacement!Existing2026"
    email = "qa+existing-membership@zestiva.test"
    user_id = str(uuid4())
    expected_statuses = ["ACTIVE", "INVITED", "REVOKED", "SUSPENDED"]
    try:
        await connection.execute("DELETE FROM users WHERE email = $1", email)
        role_id = await connection.fetchval("SELECT id::text FROM roles WHERE name = 'consultant'")
        await connection.execute(
            """INSERT INTO users
            (id,email,password_hash,role_id,is_verified,failed_login_attempts,created_at,updated_at,is_active,
             permissions,status,email_verified,mobile_verified,remember_me,mfa_enabled,current_session_version,
             refresh_token_version,must_change_password,credential_status,temporary_password_created_at,
             temporary_password_expires_at,account_classification)
            VALUES($1,$2,$3,$4,TRUE,0,$5,$5,TRUE,'[]','FIRST_LOGIN',TRUE,FALSE,FALSE,FALSE,0,0,TRUE,
                   'TEMPORARY',$5,$6,'PRODUCTION_USER')""",
            user_id,
            email,
            password_service.hash_password(temporary_password),
            role_id,
            now,
            now + timedelta(days=1),
        )
        for index, status in enumerate(expected_statuses):
            organization_id = str(uuid4())
            await connection.execute(
                "INSERT INTO organizations(id,name,status,created_at,updated_at) VALUES($1,$2,'ACTIVE',$3,$3)",
                organization_id,
                f"Membership State QA {index}",
                now,
            )
            await connection.execute(
                """INSERT INTO organization_memberships
                (id,user_id,organization_id,status,is_verified,tags,joined_at,created_at,updated_at)
                VALUES($1,$2,$3,$4,TRUE,'[]',$5,$5,$5)""",
                uuid4(),
                user_id,
                organization_id,
                status,
                now,
            )
    finally:
        await connection.close()

    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": temporary_password})
        assert login.status_code == 200, login.text
        changed = await client.post(
            "/api/v1/auth/change-temporary-password",
            headers={"Authorization": f"Bearer {login.json()['data']['tokens']['access_token']}"},
            json={
                "current_password": temporary_password,
                "new_password": replacement_password,
                "confirm_password": replacement_password,
            },
        )
        assert changed.status_code == 200, changed.text

    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    try:
        states = await connection.fetch(
            "SELECT status FROM organization_memberships WHERE user_id = $1 ORDER BY status", user_id
        )
        assert [row["status"] for row in states] == sorted(expected_statuses)
    finally:
        await connection.close()

    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        for label, user_id, email in identities:
            login = await client.post("/api/v1/auth/login", json={"email": email, "password": temporary_password})
            assert login.status_code == 200, login.text
            login_data = login.json()["data"]
            assert login_data["user"]["must_change_password"] is True
            assert login_data["user"]["workspaceAuthorities"] == []

            changed = await client.post(
                "/api/v1/auth/change-temporary-password",
                headers={"Authorization": f"Bearer {login_data['tokens']['access_token']}"},
                json={"current_password": temporary_password, "new_password": replacement_password, "confirm_password": replacement_password},
            )
            assert changed.status_code == 200, changed.text
            changed_data = changed.json()["data"]
            current = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {changed_data['tokens']['access_token']}"})
            assert current.status_code == 200, current.text
            authorities = current.json()["data"]["workspaceAuthorities"]
            expected_workspace = "senior-consultant" if label == "senior" else "internal-consultant"
            assert [(authority["workspaceId"], authority["tenantId"]) for authority in authorities] == [(expected_workspace, organization_id)]

            refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": changed_data["tokens"]["refresh_token"]})
            assert refreshed.status_code == 200, refreshed.text
            refreshed_data = refreshed.json()["data"]
            logout = await client.post("/api/v1/auth/logout", json={"refresh_token": refreshed_data["refresh_token"]})
            assert logout.status_code == 200, logout.text
            relogin = await client.post("/api/v1/auth/login", json={"email": email, "password": replacement_password})
            assert relogin.status_code == 200, relogin.text
            relogin_authorities = relogin.json()["data"]["user"]["workspaceAuthorities"]
            assert [(authority["workspaceId"], authority["tenantId"]) for authority in relogin_authorities] == [(expected_workspace, organization_id)]

    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL)
    try:
        states = await connection.fetch("SELECT u.email,u.status,m.status membership_status FROM users u JOIN organization_memberships m ON m.user_id=u.id WHERE u.email LIKE 'qa+%-journey@zestiva.test' ORDER BY u.email")
        assert [(row["status"], row["membership_status"]) for row in states] == [("ACTIVE", "ACTIVE"), ("ACTIVE", "ACTIVE")]
    finally:
        await connection.close()
