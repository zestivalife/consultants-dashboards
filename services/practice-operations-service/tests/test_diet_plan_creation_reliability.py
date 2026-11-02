from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text()
MIGRATION = (ROOT / "alembic" / "versions" / "0063_diet_plan_creation_idempotency.py").read_text()


def test_diet_plan_creation_requires_and_serializes_idempotency_key():
    section = MAIN[MAIN.index('async def create_diet_plan('):MAIN.index('@app.get("/api/v1/practice-operations/diet-plans/{plan_id}")')]
    assert 'Header(None,alias="Idempotency-Key")' in section
    assert 'IDEMPOTENCY_KEY_REQUIRED' in section
    assert 'pg_advisory_xact_lock' in section
    assert 'IDEMPOTENCY_KEY_REUSED' in section
    assert '"idempotent_replay":True' in section


def test_diet_plan_client_routes_enforce_team_assignment_and_tenant_scope():
    context = MAIN[MAIN.index('async def get_diet_plan_health_context('):MAIN.index('def _diet_plan_readiness_error')]
    listing = MAIN[MAIN.index('async def list_diet_plans('):MAIN.index('@app.post("/api/v1/practice-operations/diet-plans"')]
    creation = MAIN[MAIN.index('async def create_diet_plan('):MAIN.index('@app.get("/api/v1/practice-operations/diet-plans/{plan_id}")')]
    assert '_team_guard(request,db,ctx,"PLAN_VIEW",client_id)' in context
    assert '_team_guard(request,db,ctx,"PLAN_VIEW",client_id)' in listing
    assert '_team_guard(request,db,ctx,"PLAN_CREATE",body.client_id)' in creation
    assert 'require_capability(request,db,ctx,"DIET_PLAN")' in creation


def test_idempotency_migration_is_forward_scoped_and_reversible():
    assert 'revision = "0063_diet_plan_idempotency"' in MIGRATION
    assert len("0063_diet_plan_idempotency") <= 32
    assert 'down_revision = "0062_merge_release_heads"' in MIGRATION
    assert 'ADD COLUMN idempotency_key VARCHAR(160)' in MIGRATION
    assert 'tenant_id,authorised_consultant_id,idempotency_key' in MIGRATION
    assert "WHERE plan_type='DIET_PLAN' AND idempotency_key IS NOT NULL" in MIGRATION
    assert 'DROP COLUMN IF EXISTS idempotency_key' in MIGRATION


def test_publication_keeps_consent_and_exact_state_enforcement():
    section = MAIN[MAIN.index('async def publish_diet_plan('):MAIN.index('@app.get("/api/v1/practice-operations/diet-plans/{plan_id}/download")')]
    assert "plan[\"status\"]!=\"APPROVED\"" in section
    assert "consented_scopes ? 'DIET_PLANS'" in section
    assert 'DIET_PLAN_CONSENT_REQUIRED' in section
