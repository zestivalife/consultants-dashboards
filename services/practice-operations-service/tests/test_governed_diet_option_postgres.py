"""Atomic governed-option acceptance against isolated PostgreSQL in exact-SHA CI."""
import asyncio
from datetime import datetime, timezone
import json
import os
from uuid import uuid4

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db import get_db
from app.main import app


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="isolated PostgreSQL is required")


class ResolverResponse:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, connection_id):
        self.connection_id = connection_id

    def json(self):
        return {
            "connectionId": self.connection_id,
            "option": {
                "mealHead": "LUNCH",
                "components": [{
                    "componentId": "governed-component",
                    "foodId": "food-1",
                    "servingId": "serving-1",
                    "multiplier": 1,
                    "nutrition": {"kcal": 210, "protein": 12, "carbohydrate": 28, "fat": 5, "fibre": 4},
                }],
                "nutrition": {"kcal": 210, "protein": 12, "carbohydrate": 28, "fat": 5, "fibre": 4},
                "optionHash": "authoritative-hash",
                "calculationStatus": "AUTHORITATIVELY_RESOLVED",
                "clinicalApproval": False,
            },
        }


@pytest.mark.asyncio
async def test_governed_option_is_atomic_immutable_idempotent_and_authoritative(monkeypatch):
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    tenant, consultant, client_id = f"tenant-{uuid4()}", f"consultant-{uuid4()}", f"client-{uuid4()}"
    plan_id, version_id, connection_id = uuid4(), uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    monkeypatch.setenv("EXTERNAL_FITEATSY_BACKEND_URL", "https://fiteatsy.invalid")
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY", private_pem)
    monkeypatch.setenv("EXTERNAL_FITEATSY_OUTBOUND_KEY_ID", "ci-key")
    get_settings.cache_clear()

    async def database():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = database
    async with sessions() as session:
        await session.execute(text("""INSERT INTO external_profession_plans
          (id,tenant_id,client_id,profession_code,plan_type,title,status,current_version,created_by,authorised_consultant_id,daily_calories_target,daily_protein_target_g,created_at,updated_at)
          VALUES (:id,:tenant,:client,'DIETITIAN','DIET_PLAN','CI governed plan','DRAFT',1,:actor,:actor,1800,90,:now,:now)"""),
          {"id":plan_id,"tenant":tenant,"client":client_id,"actor":consultant,"now":now})
        await session.execute(text("""INSERT INTO external_profession_plan_versions
          (id,plan_id,tenant_id,client_id,version,status,title,nutrition_snapshot,created_by,created_at)
          VALUES (:id,:plan,:tenant,:client,1,'DRAFT','CI governed plan','{}'::jsonb,:actor,:now)"""),
          {"id":version_id,"plan":plan_id,"tenant":tenant,"client":client_id,"actor":consultant,"now":now})
        await session.execute(text("""INSERT INTO external_fiteatsy_connections
          (id,tenant_id,consultant_id,fiteatsy_user_id,consultant_client_id,state,consent_version,consented_scopes,programme_status,connected_at,updated_at)
          VALUES (:id,:tenant,:actor,:user,:client,'ACTIVE','v1',CAST(:scopes AS jsonb),'ACTIVE',:now,:now)"""),
          {"id":connection_id,"tenant":tenant,"actor":consultant,"user":f"fiteatsy-{uuid4()}","client":client_id,"scopes":json.dumps(["DIET_PLANS"]),"now":now})
        await session.commit()

    calls = []
    browser_client = httpx.AsyncClient
    class ResolverClient:
        def __init__(self, **_kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return False
        async def post(self, url, headers, json):
            calls.append((url, headers, json))
            return ResolverResponse(str(connection_id))
    monkeypatch.setattr("app.main.httpx.AsyncClient", ResolverClient)

    headers={"X-User-Id":consultant,"X-Tenant-Id":tenant,"X-User-Role":"EXTERNAL_CONSULTANT","X-Tenant-Type":"PRACTICE","Idempotency-Key":"option-operation-1"}
    payload={"expected_version":1,"meal_head":"LUNCH","components":[{"food_id":"food-1","serving_id":"serving-1","multiplier":1}]}
    transport=httpx.ASGITransport(app=app)
    async with browser_client(transport=transport,base_url="http://test") as browser:
        first=await browser.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/options/lunch-option-1",headers=headers,json=payload)
        assert first.status_code==200,first.text
        assert first.json()["data"]["version"]==2
        assert first.json()["data"]["option"]["nutrition"]["kcal"]==210
        replay=await browser.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/options/lunch-option-1",headers=headers,json=payload)
        assert replay.status_code==200
        assert replay.json()["data"]["plan_version_id"]==first.json()["data"]["plan_version_id"]
        stale_headers={**headers,"Idempotency-Key":"option-operation-2"}
        stale=await browser.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/options/lunch-option-1",headers=stale_headers,json=payload)
        assert stale.status_code==409
        assert stale.json()["error"]["code"]=="STALE_WRITE"
        tampered={
            "expected_version":2,
            "options":[{
                "combinationId":"lunch-option-1","mealHead":"LUNCH","selected":True,
                "nutrition":{"kcal":999999,"protein":999999},
                "components":[{"foodId":"food-1","servingId":"serving-1","multiplier":1,"nutrition":{"kcal":999999}}],
            }],
        }
        competing=await asyncio.gather(
            browser.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/draft",headers=headers,json=tampered),
            browser.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/draft",headers=headers,json=tampered),
        )
        assert sorted(response.status_code for response in competing)==[200,409]
        saved=next(response for response in competing if response.status_code==200)
        assert saved.status_code==200,saved.text
        assert saved.json()["data"]["version"]==3
        assert saved.json()["data"]["nutrition"]["actual_calories"]==210
        assert saved.json()["data"]["options"][0]["nutrition"]["kcal"]==210
        assert saved.json()["data"]["options"][0]["calculationStatus"]=="AUTHORITATIVELY_RESOLVED"
        other_tenant=await browser.get(f"/api/v1/practice-operations/diet-plans/{plan_id}",headers={**headers,"X-Tenant-Id":f"other-{tenant}"})
        assert other_tenant.status_code==404
        async with sessions() as session:
            await session.execute(text("UPDATE external_fiteatsy_connections SET state='REVOKED' WHERE id=:id"),{"id":connection_id})
            await session.commit()
        revoked=await browser.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/draft",headers=headers,json={**tampered,"expected_version":3})
        assert revoked.status_code==403
        assert revoked.json()["error"]["code"]=="DIET_PLAN_CONSENT_REQUIRED"

    async with sessions() as session:
        versions=(await session.execute(text("SELECT version,status FROM external_profession_plan_versions WHERE plan_id=:plan ORDER BY version"),{"plan":plan_id})).all()
        # A fresh session is the persistence/reopen boundary. The exact stored
        # immutable version must retain the resolver-owned nutrition snapshot.
        item=(await session.execute(text("""SELECT i.content FROM external_profession_plan_items i
          JOIN external_profession_plan_sections s ON s.id=i.plan_section_id
          JOIN external_profession_plan_versions v ON v.id=s.plan_version_id
          WHERE v.plan_id=:plan AND v.version=3"""),{"plan":plan_id})).scalar_one()
        events=(await session.execute(text("SELECT COUNT(*) FROM external_profession_plan_audit_events WHERE plan_id=:plan AND event_type='OPTION_UPDATED'"),{"plan":plan_id})).scalar_one()
        assert versions==[(1,"DRAFT"),(2,"SAVED"),(3,"SAVED")]
        assert item["nutrition"]["kcal"]==210 and item["calculationStatus"]=="AUTHORITATIVELY_RESOLVED"
        assert events==1
    assert len(calls)==4  # First write, stale operation, and both concurrent authoritative draft attempts.
    app.dependency_overrides.clear();get_settings.cache_clear();await engine.dispose()
