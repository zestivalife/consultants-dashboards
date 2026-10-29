"""PostgreSQL acceptance for the Connection PIN redemption boundary.

This test is skipped during lightweight local runs and is mandatory in exact-SHA
CI, where TEST_DATABASE_URL points at an isolated PostgreSQL 16 service whose
migrations have already been applied.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from uuid import uuid4

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db import get_db
from app.fiteatsy_connections import build_router, pin_verifier


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="isolated PostgreSQL is required")


def _error(request: Request, status: int, code: str, message: str, retryable: bool = False):
    return JSONResponse(status_code=status, content={"success": False, "error": {"code": code, "safe_message": message, "retryable": retryable}})


async def _context():
    return {"user_id": "consultant-1", "tenant_id": "tenant-1", "tenant_type": "PRACTICE"}


def _external_only(_request, _context):
    return None


def _assertion(private_key, user_id: str, purpose: str = "consultant_connection") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user_id,
        "actor_type": "FITEATSY_USER",
        "purpose": purpose,
        "iss": "fiteatsy-ci",
        "aud": "practice-operations-ci",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }, private_key, algorithm="RS256")


@pytest.mark.asyncio
async def test_redeem_is_atomic_replay_safe_and_user_bound(monkeypatch):
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    monkeypatch.setenv("EXTERNAL_FITEATSY_CONNECTION_ENABLED", "true")
    monkeypatch.setenv("EXTERNAL_FITEATSY_PIN_PEPPER", "ci-pepper")
    monkeypatch.setenv("EXTERNAL_FITEATSY_INBOUND_PUBLIC_KEY", public_pem)
    monkeypatch.setenv("EXTERNAL_FITEATSY_INBOUND_ISSUER", "fiteatsy-ci")
    monkeypatch.setenv("EXTERNAL_FITEATSY_INBOUND_AUDIENCE", "practice-operations-ci")
    get_settings.cache_clear()

    async def database():
        async with sessions() as session:
            yield session

    app = FastAPI()
    app.include_router(build_router(_context, _external_only, _error))
    app.dependency_overrides[get_db] = database

    pin = "012345"
    invitation_id = uuid4()
    now = datetime.now(timezone.utc)
    async with sessions() as session:
        await session.execute(text("DELETE FROM external_fiteatsy_connection_events"))
        await session.execute(text("DELETE FROM external_fiteatsy_consents"))
        await session.execute(text("DELETE FROM external_fiteatsy_connections"))
        await session.execute(text("DELETE FROM external_fiteatsy_connection_invitations"))
        await session.execute(text("""INSERT INTO external_fiteatsy_connection_invitations
          (id,tenant_id,consultant_id,pin_verifier,pin_hint,status,attempt_count,max_attempts,expires_at,requested_scopes,created_at,updated_at)
          VALUES (:id,'tenant-1','consultant-1',:verifier,'45','PENDING',0,8,:expires,CAST(:scopes AS JSONB),:now,:now)"""), {
            "id": invitation_id,
            "verifier": pin_verifier(pin, "ci-pepper"),
            "expires": now + timedelta(hours=1),
            "scopes": json.dumps(["PROFILE", "DIET_PLANS"]),
            "now": now,
        })
        await session.commit()

    body = {
        "pin": pin,
        "purpose": "CONSULTANT_CONNECTION_PIN",
        "consent_version": "external-consultant-v1",
        "accepted_scopes": ["PROFILE", "DIET_PLANS"],
    }
    replay_key = str(uuid4())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {_assertion(key, 'fiteatsy-user-1')}", "Idempotency-Key": replay_key}
        first = await client.post("/api/v1/fiteatsy-connections/redeem", json=body, headers=headers)
        assert first.status_code == 201, first.text
        assert first.json()["data"]["state"] == "ACTIVE"
        connection_id = first.json()["data"]["connection_id"]

        replay = await client.post("/api/v1/fiteatsy-connections/redeem", json=body, headers=headers)
        assert replay.status_code == 200, replay.text
        assert replay.json()["data"]["connection_id"] == connection_id

        other_user = {"Authorization": f"Bearer {_assertion(key, 'fiteatsy-user-2')}", "Idempotency-Key": replay_key}
        rejected = await client.post("/api/v1/fiteatsy-connections/redeem", json=body, headers=other_user)
        assert rejected.status_code == 409
        assert rejected.json()["error"]["code"] == "CONNECTION_PIN_ALREADY_USED"

        login_assertion = {"Authorization": f"Bearer {_assertion(key, 'fiteatsy-user-1', 'login_pin')}", "Idempotency-Key": str(uuid4())}
        rejected_login = await client.post("/api/v1/fiteatsy-connections/redeem", json=body, headers=login_assertion)
        assert rejected_login.status_code == 401

    async with sessions() as session:
        connections = (await session.execute(text("SELECT COUNT(*) FROM external_fiteatsy_connections"))).scalar_one()
        consents = (await session.execute(text("SELECT COUNT(*) FROM external_fiteatsy_consents"))).scalar_one()
        invitation = (await session.execute(text("SELECT status,redeemed_by_fiteatsy_user_id FROM external_fiteatsy_connection_invitations WHERE id=:id"), {"id": invitation_id})).mappings().one()
        assert connections == 1
        assert consents == 1
        assert invitation["status"] == "REDEEMED"
        assert invitation["redeemed_by_fiteatsy_user_id"] == "fiteatsy-user-1"

    get_settings.cache_clear()
    await engine.dispose()
