import os
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import asyncpg
import httpx
import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


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


def practitioner_headers(user: str = "diet-consultant", role: str = "CONSULTANT") -> dict[str, str]:
    return {"X-User-Id": user, "X-Tenant-Id": "diet-tenant", "X-Tenant-Type": "PRACTICE", "X-User-Role": role, "X-Profession-Code": "NUTRITIONIST"}


async def seed_lifecycle() -> tuple[str, str]:
    connection = await asyncpg.connect(INTEGRATION_DATABASE_URL);now = datetime.now(timezone.utc)
    assessment_id, connection_id = str(uuid4()), str(uuid4())
    try:
        await connection.execute("TRUNCATE external_fiteatsy_connections, external_diet_plan_assessment_links, external_profession_plan_audit_events, external_profession_plan_items, external_profession_plan_sections, external_profession_plan_versions, external_profession_plans, external_nutrition_assessment_versions, external_nutrition_assessments CASCADE")
        await connection.execute("""INSERT INTO practice_tenant_configuration
          (tenant_id,profession,capabilities,terminology,profile,version,updated_by,updated_at)
          VALUES('diet-tenant','NUTRITIONIST','[\"CLIENT_CRM\",\"DIET_PLAN\"]','{}','{}',1,'fixture',$1)
          ON CONFLICT(tenant_id) DO UPDATE SET profession=EXCLUDED.profession,capabilities=EXCLUDED.capabilities,updated_at=EXCLUDED.updated_at""", now)
        await connection.execute("""INSERT INTO external_nutrition_assessments
          (id,tenant_id,client_id,authorised_consultant_id,status,current_version,review_state,consent_state,stale,created_at,updated_at,readiness_status)
          VALUES($1,'diet-tenant','diet-client','diet-consultant','REVIEWED',1,'REVIEWED','CONSENTED',FALSE,$2,$2,'READY')""", assessment_id, now)
        await connection.execute("""INSERT INTO external_nutrition_assessment_versions
          (id,assessment_id,tenant_id,client_id,version,source_manifest,calculation_methodologies,calculations,input_completeness,clinical_safety_findings,nutrition_considerations,provenance,fingerprint_sha256,created_by,created_at,reviewed_by,reviewed_at,assessment_data,readiness)
          VALUES($1,$2,'diet-tenant','diet-client',1,'[]','{}','{}','{}','{}','{}','{}',$3,'diet-consultant',$4,'senior-reviewer',$4,'{}','{}')""", uuid4(), assessment_id, "a" * 64, now)
        await connection.execute("""INSERT INTO external_fiteatsy_connections
          (id,tenant_id,consultant_id,fiteatsy_user_id,consultant_client_id,state,consent_version,consented_scopes,programme_status,connected_at,updated_at)
          VALUES($1,'diet-tenant','diet-consultant','mobile-diet-client','diet-client','ACTIVE','v1','[\"DIET_PLANS\"]','ACTIVE',$2,$2)""", connection_id, now)
    finally: await connection.close()
    return assessment_id, connection_id


@pytest.mark.asyncio
async def test_real_http_exact_version_review_publication_mobile_and_docx_lifecycle(monkeypatch):
    assessment_id, connection_id = await seed_lifecycle()
    from app.config import get_settings
    settings=get_settings();settings.external_fiteatsy_connection_enabled=True;settings.external_fiteatsy_diet_publish_enabled=True
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    settings.external_fiteatsy_inbound_public_key=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    async def resolve_governed_option(_request, connection, _plan, resolver_body, _purpose="external_consultant_diet_option"):
        component = resolver_body["components"][0]
        return {
            "mealHead": resolver_body["mealHead"],
            "components": [{
                "componentId": "governed-component",
                **component,
                "nutrition": {"kcal": 420, "protein": 18},
            }],
            "nutrition": {"kcal": 420, "protein": 18},
            "optionHash": "authoritative-breakfast-hash",
            "calculationStatus": "AUTHORITATIVELY_RESOLVED",
            "clinicalApproval": False,
        }, None
    monkeypatch.setattr("app.main._resolve_governed_option", resolve_governed_option)
    async def deliver_published_plan(_request, _connection, plan, _options, _published_at):
        return {
            "ingestion": {"planId": str(plan["id"]), "versionId": f'{plan["id"]}:3'},
            "selection": {"activePlanId": str(plan["id"])},
        }, None
    monkeypatch.setattr("app.main._deliver_diet_plan_to_fiteatsy", deliver_published_plan)
    from app.main import app
    transport=httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport,base_url="http://test") as client:
        create_headers={**practitioner_headers(),"Idempotency-Key":"diet-plan-create-1"}
        create_payload={"client_id":"diet-client","name":"QA exact plan","daily_calories_target":2000,"daily_protein_target_g":90,"health_goals":["ENERGY"]}
        created=await client.post("/api/v1/practice-operations/diet-plans",headers=create_headers,json=create_payload)
        assert created.status_code==201;plan_id=created.json()["data"]["id"]
        replayed=await client.post("/api/v1/practice-operations/diet-plans",headers=create_headers,json=create_payload)
        assert replayed.status_code==201 and replayed.json()["data"]["id"]==plan_id and replayed.json()["data"]["idempotent_replay"] is True
        key_reused=await client.post("/api/v1/practice-operations/diet-plans",headers=create_headers,json={**create_payload,"name":"Different request"})
        assert key_reused.status_code==409 and key_reused.json()["error"]["code"]=="IDEMPOTENCY_KEY_REUSED"
        options=[{"combinationId":"breakfast-1","mealHead":"BREAKFAST","clientTitle":"Oats and fruit","selected":True,"nutrition":{"kcal":999999,"protein":999999},"components":[{"foodId":"food-oats","servingId":"serving-bowl","multiplier":1}]}]
        saved=await client.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/draft",headers=practitioner_headers(),json={"expected_version":1,"options":options})
        assert saved.status_code==200 and saved.json()["data"]["version"]==2
        premature=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/publish",headers=practitioner_headers())
        assert premature.status_code==409 and premature.json()["error"]["code"]=="DIET_PLAN_APPROVAL_REQUIRED"
        submitted=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/review",headers=practitioner_headers(),json={"action":"SUBMIT","expected_version":2})
        assert submitted.status_code==200
        changes=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/review",headers=practitioner_headers("senior-reviewer","SENIOR_CONSULTANT"),json={"action":"REQUEST_CHANGES","expected_version":2,"reason":"Clarify portions"})
        assert changes.status_code==200 and changes.json()["data"]["status"]=="CHANGES_REQUESTED"
        resubmitted=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/review",headers=practitioner_headers(),json={"action":"SUBMIT","expected_version":2})
        assert resubmitted.status_code==200
        concurrent=await client.put(f"/api/v1/practice-operations/diet-plans/{plan_id}/draft",headers=practitioner_headers(),json={"expected_version":2,"options":options})
        assert concurrent.status_code==200 and concurrent.json()["data"]["version"]==3
        stale_approval=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/review",headers=practitioner_headers("senior-reviewer","SENIOR_CONSULTANT"),json={"action":"APPROVE","expected_version":2})
        assert stale_approval.status_code==409 and stale_approval.json()["error"]["code"]=="STALE_WRITE"
        approved=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/review",headers=practitioner_headers(),json={"action":"APPROVE","expected_version":3})
        assert approved.status_code==200 and approved.json()["data"]["version"]==3
        unauthorised=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/publish",headers=practitioner_headers("other-consultant"))
        assert unauthorised.status_code==404

        database=await asyncpg.connect(INTEGRATION_DATABASE_URL)
        try:
            await database.execute("""INSERT INTO external_diet_plan_assessment_links
              (id,tenant_id,client_id,external_plan_id,external_plan_version,assessment_id,assessment_version,calculation_methodologies,plan_state,legacy_lineage_state,created_by,created_at)
              VALUES($1,'diet-tenant','diet-client',$2,'3',$3,1,'{}','APPROVED','LINKED','diet-consultant',$4)""",uuid4(),plan_id,assessment_id,datetime.now(timezone.utc))
        finally: await database.close()
        published=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/publish",headers=practitioner_headers())
        assert published.status_code==200 and published.json()["data"]["version"]==3
        repeated=await client.post(f"/api/v1/practice-operations/diet-plans/{plan_id}/publish",headers=practitioner_headers())
        assert repeated.status_code==200 and repeated.json()["data"]["already_published"] is True
        docx=await client.get(f"/api/v1/practice-operations/diet-plans/{plan_id}/download",headers=practitioner_headers())
        assert docx.status_code==200 and docx.content.startswith(b"PK") and docx.headers["x-diet-plan-version"]=="3"

        database=await asyncpg.connect(INTEGRATION_DATABASE_URL)
        try:
            publication=await database.fetchrow("SELECT plan_version,content FROM external_fiteatsy_plan_publications WHERE connection_id=$1",connection_id)
            assert publication["plan_version"]==3
            published_options=json.loads(publication["content"])["mealOptions"]
            assert published_options[0]["combinationId"]=="breakfast-1"
            assert published_options[0]["calculationStatus"]=="AUTHORITATIVELY_RESOLVED"
            assert published_options[0]["nutrition"]=={"kcal":420,"protein":18}
        finally: await database.close()

        now=datetime.now(timezone.utc);claims={"iss":settings.external_fiteatsy_inbound_issuer,"aud":settings.external_fiteatsy_inbound_audience,"sub":"mobile-diet-client","actor_type":"FITEATSY_USER","iat":int(now.timestamp()),"exp":int((now+timedelta(minutes=5)).timestamp())}
        token=jwt.encode(claims,key,algorithm="RS256")
        mobile=await client.get(f"/api/v1/fiteatsy-connections/{connection_id}/diet-plans",headers={"Authorization":f"Bearer {token}"})
        assert mobile.status_code==200
        assert mobile.json()["data"]["plans"][0]["plan_version"]==3
        mobile_option=mobile.json()["data"]["plans"][0]["content"]["mealOptions"][0]
        assert mobile_option["calculationStatus"]=="AUTHORITATIVELY_RESOLVED"
        assert mobile_option["nutrition"]=={"kcal":420,"protein":18}
        database=await asyncpg.connect(INTEGRATION_DATABASE_URL)
        try: await database.execute("UPDATE external_fiteatsy_connections SET state='REVOKED',disconnected_at=$2 WHERE id=$1",connection_id,datetime.now(timezone.utc))
        finally: await database.close()
        revoked=await client.get(f"/api/v1/fiteatsy-connections/{connection_id}/diet-plans",headers={"Authorization":f"Bearer {token}"})
        assert revoked.status_code==200 and revoked.json()["data"]["plans"]==[]

        rejected_plan=await client.post("/api/v1/practice-operations/diet-plans",headers={**practitioner_headers(),"Idempotency-Key":"diet-plan-create-rejected"},json={"client_id":"diet-client","name":"Rejected QA plan","daily_calories_target":1800,"daily_protein_target_g":80,"health_goals":[]})
        rejected_id=rejected_plan.json()["data"]["id"]
        await client.post(f"/api/v1/practice-operations/diet-plans/{rejected_id}/review",headers=practitioner_headers(),json={"action":"SUBMIT","expected_version":1})
        rejection=await client.post(f"/api/v1/practice-operations/diet-plans/{rejected_id}/review",headers=practitioner_headers("senior-reviewer","SENIOR_CONSULTANT"),json={"action":"REJECT","expected_version":1,"reason":"Unsafe clinical assumptions"})
        assert rejection.status_code==200 and rejection.json()["data"]["status"]=="REJECTED"
        rejected_publish=await client.post(f"/api/v1/practice-operations/diet-plans/{rejected_id}/publish",headers=practitioner_headers())
        assert rejected_publish.status_code==409 and rejected_publish.json()["error"]["code"]=="DIET_PLAN_APPROVAL_REQUIRED"
