"""PostgreSQL acceptance for the canonical Fiteatsy directory projection."""
from datetime import datetime, timedelta, timezone
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
from app.fiteatsy_client_directory import build_router


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="isolated PostgreSQL is required")


def _error(request: Request, status: int, code: str, message: str, retryable: bool = False):
    return JSONResponse(status_code=status, content={"success": False, "error": {"code": code, "safe_message": message, "retryable": retryable}})


async def _owner_context():
    return {"user_id": "owner-1", "role": "PLATFORM_OWNER"}


def _assertion(private_key, purpose="client_directory_sync"):
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": "fiteatsy-client-directory-sync", "actor_type": "FITEATSY_SERVICE", "purpose": purpose,
        "iss": "fiteatsy-ci", "aud": "practice-operations-ci", "iat": now,
        "exp": now + timedelta(minutes=5), "jti": str(uuid4()),
    }, private_key, algorithm="RS256")


@pytest.mark.asyncio
async def test_directory_event_is_idempotent_ordered_and_searchable(monkeypatch):
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    monkeypatch.setenv("EXTERNAL_FITEATSY_INBOUND_PUBLIC_KEY", public_pem)
    monkeypatch.setenv("EXTERNAL_FITEATSY_INBOUND_ISSUER", "fiteatsy-ci")
    monkeypatch.setenv("EXTERNAL_FITEATSY_INBOUND_AUDIENCE", "practice-operations-ci")
    get_settings.cache_clear()

    async def database():
        async with sessions() as session:
            yield session

    app = FastAPI()
    app.include_router(build_router(_owner_context, _error))
    app.dependency_overrides[get_db] = database
    user_id, event_id = uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    payload = {
        "event_id": str(event_id), "event_type": "FITEATSY_USER_REGISTERED",
        "fiteatsy_user_id": str(user_id), "source_version": 2, "schema_version": 1,
        "occurred_at": now.isoformat(), "data": {
            "fiteatsy_user_id": str(user_id), "fiteatsy_client_id": None, "display_name": "Directory Acceptance",
            "mobile_number_normalized": "+919700009904", "email_normalized": "directory@example.com",
            "account_status": "ACTIVE", "mobile_verified": True, "registration_status": "COMPLETED",
            "registered_at": now.isoformat(), "source_updated_at": now.isoformat(), "deleted_at": None,
        },
    }
    headers = {"Authorization": f"Bearer {_assertion(key)}", "Idempotency-Key": str(event_id)}
    transport = httpx.ASGITransport(app=app)
    async with sessions() as session:
        await session.execute(text("DELETE FROM fiteatsy_client_directory_events"))
        await session.execute(text("DELETE FROM fiteatsy_client_directory"))
        await session.commit()

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        applied = await client.post("/api/v1/internal/fiteatsy-client-directory/events", json=payload, headers=headers)
        assert applied.status_code == 202, applied.text
        assert applied.json()["data"]["disposition"] == "APPLIED"
        duplicate = await client.post("/api/v1/internal/fiteatsy-client-directory/events", json=payload, headers=headers)
        assert duplicate.status_code == 200
        assert duplicate.json()["data"]["disposition"] == "DUPLICATE"
        conflict = await client.post(
            "/api/v1/internal/fiteatsy-client-directory/events",
            json={**payload, "data": {**payload["data"], "display_name": "Conflicting replay"}},
            headers=headers,
        )
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "DIRECTORY_IDEMPOTENCY_CONFLICT"

        stale_payload = {**payload, "event_id": str(uuid4()), "source_version": 1,
                         "data": {**payload["data"], "display_name": "Must Not Replace"}}
        stale_headers = {"Authorization": f"Bearer {_assertion(key)}", "Idempotency-Key": stale_payload["event_id"]}
        stale = await client.post("/api/v1/internal/fiteatsy-client-directory/events", json=stale_payload, headers=stale_headers)
        assert stale.status_code == 202
        assert stale.json()["data"]["disposition"] == "STALE"

        listing = await client.get("/api/v1/practice-operations/fiteatsy-client-directory?q=9700009904&page=1&page_size=10")
        assert listing.status_code == 200, listing.text
        assert listing.json()["data"]["pagination"]["total"] == 1
        assert listing.json()["data"]["clients"][0]["display_name"] == "Directory Acceptance"

        wrong_purpose = {"Authorization": f"Bearer {_assertion(key, 'consultant_connection')}", "Idempotency-Key": str(uuid4())}
        rejected = await client.post("/api/v1/internal/fiteatsy-client-directory/events", json={**payload, "event_id": wrong_purpose["Idempotency-Key"]}, headers=wrong_purpose)
        assert rejected.status_code == 401

    get_settings.cache_clear()
    await engine.dispose()
