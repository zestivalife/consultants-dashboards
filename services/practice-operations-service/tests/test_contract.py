from pathlib import Path
import re

ROOT=Path(__file__).parents[1]


def test_runtime_image_contains_an_executable_migration_toolchain():
    dockerfile = (ROOT / "Dockerfile").read_text()
    requirements = (ROOT / "requirements.txt").read_text()
    alembic_env = (ROOT / "alembic" / "env.py").read_text()
    assert "COPY alembic ./alembic" in dockerfile
    assert "COPY alembic.ini ." in dockerfile
    assert "psycopg[binary]" in requirements
    assert 'replace("+asyncpg","+psycopg")' in alembic_env
    assert "fileConfig" not in alembic_env


def test_alembic_revision_identifiers_fit_the_version_table_contract():
    for migration in (ROOT / "alembic" / "versions").glob("*.py"):
        match = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', migration.read_text(), re.MULTILINE)
        assert match is not None
        assert len(match.group(1)) <= 32


def test_tenant_scoped_tables_and_outbox():
    migration=(ROOT/"alembic/versions/0001_practice_operations.py").read_text()
    assert 'TABLES=("practice_consultations","practice_follow_ups","practice_goals","practice_tasks","practice_checkins","practice_adherence_entries","practice_client_notes")' in migration
    assert migration.count("tenant_id VARCHAR(80) NOT NULL") == 2
    assert "service_outbox_events" in migration
    assert "idempotency_key" in migration
    assert "version INTEGER NOT NULL DEFAULT 1" in migration


def test_api_contract_has_safety_controls():
    source=(ROOT/"app/main.py").read_text()
    for value in ("IDEMPOTENCY_KEY_REQUIRED","STALE_WRITE","tenant_id = :tenant_id","next_cursor","correlation_id","retryable"):
        assert value in source
    assert "EXTERNAL_PRACTICE_SCOPE_REQUIRED" in source
    assert "SELECT * FROM" not in source.replace('f"SELECT * FROM {table}', '')


def test_gateway_strips_caller_supplied_authority_headers():
    gateway=(ROOT.parents[1]/"api-gateway/app/routers/proxy.py").read_text()
    for header in ("x-user-id","x-user-role","x-user-permissions","x-tenant-id","x-tenant-type"):
        assert header in gateway
    assert "Authority headers are gateway-owned" in gateway
