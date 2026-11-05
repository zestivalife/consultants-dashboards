from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest


ADMIN_URL = os.getenv("MIGRATION_TEST_ADMIN_URL")
SERVICE_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    not ADMIN_URL,
    reason="MIGRATION_TEST_ADMIN_URL is required for destructive disposable-database tests",
)


def _database_url(name: str) -> str:
    parsed = urlsplit(ADMIN_URL)
    return urlunsplit((parsed.scheme, parsed.netloc, f"/{name}", parsed.query, parsed.fragment))


def _alembic_url(name: str) -> str:
    return _database_url(name).replace("postgresql://", "postgresql+psycopg://", 1)


def _upgrade(name: str, revision: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = _alembic_url(name)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        cwd=SERVICE_ROOT,
        env=env,
        check=True,
    )


@pytest.fixture(params=["production", "release"])
def migrated_database(request):
    name = f"zestiva_lineage_{request.param}_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    try:
        initial_head = (
            "0061_fiteatsy_directory"
            if request.param == "production"
            else "0060_diet_rejection"
        )
        _upgrade(name, initial_head)
        yield request.param, name
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
            admin.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (name,),
            )
            admin.execute(f'DROP DATABASE IF EXISTS "{name}"')


def _seed_shared_records(connection: psycopg.Connection) -> dict[str, str]:
    assignment_id = uuid.uuid4()
    connection_id = uuid.uuid4()
    consent_id = uuid.uuid4()
    connection.execute(
        """INSERT INTO external_client_team_assignments
        (id, tenant_id, client_id, user_id, assignment_role, assigned_by, assigned_at)
        VALUES (%s, 'tenant-sentinel', 'client-sentinel', 'consultant-sentinel',
                'PRIMARY_PRACTITIONER', 'super-admin-sentinel', NOW())""",
        (assignment_id,),
    )
    connection.execute(
        """INSERT INTO external_fiteatsy_connections
        (id, tenant_id, consultant_id, fiteatsy_user_id, consultant_client_id,
         state, consent_version, consented_scopes, programme_status,
         connected_at, updated_at)
        VALUES (%s, 'tenant-sentinel', 'consultant-sentinel', 'fit-user-sentinel',
                'client-sentinel', 'ACTIVE', 'v1', '["profile"]'::jsonb,
                'ACTIVE', NOW(), NOW())""",
        (connection_id,),
    )
    connection.execute(
        """INSERT INTO external_fiteatsy_consents
        (id, connection_id, consent_version, scopes, decision,
         actor_fiteatsy_user_id, created_at)
        VALUES (%s, %s, 'v1', '["profile"]'::jsonb, 'GRANTED',
                'fit-user-sentinel', NOW())""",
        (consent_id, connection_id),
    )
    return {
        "assignment_id": str(assignment_id),
        "connection_id": str(connection_id),
        "consent_id": str(consent_id),
    }


def _simulate_external_measurement_ledger(connection: psycopg.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS external_client_measurements (
      id UUID PRIMARY KEY, series_id UUID NOT NULL, tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL, measurement_type VARCHAR(40) NOT NULL,
      value NUMERIC(10,3) NOT NULL, unit VARCHAR(12) NOT NULL, measured_at TIMESTAMPTZ NOT NULL,
      source VARCHAR(40) NOT NULL, recorded_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      version INTEGER NOT NULL CHECK(version > 0), supersedes_id UUID REFERENCES external_client_measurements(id) ON DELETE RESTRICT,
      correction_reason TEXT, UNIQUE(series_id,version),
      CHECK(measurement_type IN ('HEIGHT_CM','WEIGHT_KG','WAIST_CM','HIP_CM','NECK_CM','CHEST_CM','MID_UPPER_ARM_CM','THIGH_CM','CALF_CM')),
      CHECK(source IN ('CLIENT_REPORTED','PROFESSIONALLY_RECORDED','DOCUMENT_DERIVED')),
      CHECK((measurement_type='WEIGHT_KG' AND unit='kg') OR (measurement_type<>'WEIGHT_KG' AND unit='cm')),
      CHECK(value > 0), CHECK((version=1 AND supersedes_id IS NULL AND correction_reason IS NULL) OR
                              (version>1 AND supersedes_id IS NOT NULL AND length(correction_reason)>=3)))""")
    connection.execute("CREATE INDEX IF NOT EXISTS ix_external_client_measurements_latest ON external_client_measurements(tenant_id,client_id,measurement_type,measured_at DESC,version DESC)")
    connection.execute("CREATE INDEX IF NOT EXISTS ix_external_client_measurements_series ON external_client_measurements(tenant_id,client_id,series_id,version DESC)")


def _seed_production_directory(connection: psycopg.Connection) -> dict[str, str]:
    directory_id = uuid.uuid4()
    fiteatsy_user_id = uuid.uuid4()
    event_id = uuid.uuid4()
    reconciliation_id = uuid.uuid4()
    connection.execute(
        """INSERT INTO fiteatsy_client_directory
        (id, fiteatsy_user_id, fiteatsy_client_id, display_name,
         account_status, mobile_verified, registration_status, registered_at,
         source_updated_at, source_version, last_synced_at, sync_status,
         created_at, updated_at)
        VALUES (%s, %s, 'fit-client-sentinel', 'Directory Sentinel', 'ACTIVE',
                TRUE, 'COMPLETED', NOW(), NOW(), 7, NOW(), 'CURRENT', NOW(), NOW())""",
        (directory_id, fiteatsy_user_id),
    )
    connection.execute(
        """INSERT INTO fiteatsy_client_directory_events
        (event_id, event_type, fiteatsy_user_id, source_version, schema_version,
         payload_sha256, occurred_at, processed_at, disposition)
        VALUES (%s, 'CLIENT_UPDATED', %s, 7, 1, %s, NOW(), NOW(), 'APPLIED')""",
        (event_id, fiteatsy_user_id, "a" * 64),
    )
    connection.execute(
        """INSERT INTO fiteatsy_client_directory_reconciliation_runs
        (id, started_at, completed_at, source_count, destination_count,
         missing_count, stale_count, duplicate_count, status)
        VALUES (%s, NOW(), NOW(), 1, 1, 0, 0, 0, 'COMPLETED')""",
        (reconciliation_id,),
    )
    return {
        "directory_id": str(directory_id),
        "event_id": str(event_id),
        "reconciliation_id": str(reconciliation_id),
    }


def test_both_migration_heads_converge_without_losing_records(migrated_database):
    path, name = migrated_database
    url = _database_url(name)
    with psycopg.connect(url) as connection:
        if path == "production":
            _simulate_external_measurement_ledger(connection)
        sentinels = _seed_shared_records(connection)
        if path == "production":
            sentinels.update(_seed_production_directory(connection))
        connection.commit()

    _upgrade(name, "head")

    with psycopg.connect(url) as connection:
        assert connection.execute(
            "SELECT version_num FROM practice_operations_alembic_version"
        ).fetchall() == [("0064_external_practice_clients",)]
        assert connection.execute(
            "SELECT id::text FROM external_client_team_assignments WHERE id = %s",
            (sentinels["assignment_id"],),
        ).fetchone() == (sentinels["assignment_id"],)
        assert connection.execute(
            "SELECT id::text FROM external_fiteatsy_connections WHERE id = %s",
            (sentinels["connection_id"],),
        ).fetchone() == (sentinels["connection_id"],)
        assert connection.execute(
            "SELECT connection_id::text FROM external_fiteatsy_consents WHERE id = %s",
            (sentinels["consent_id"],),
        ).fetchone() == (sentinels["connection_id"],)
        assert connection.execute(
            "SELECT to_regclass('public.external_client_measurements')::text"
        ).fetchone() == ("external_client_measurements",)
        assert connection.execute(
            "SELECT to_regclass('public.external_fiteatsy_pin_attempt_limits')::text"
        ).fetchone() == ("external_fiteatsy_pin_attempt_limits",)
        assert connection.execute(
            "SELECT to_regclass('public.fiteatsy_client_directory')::text"
        ).fetchone() == ("fiteatsy_client_directory",)
        assert connection.execute(
            "SELECT to_regclass('public.external_practice_clients')::text"
        ).fetchone() == ("external_practice_clients",)
        assert connection.execute(
            "SELECT data_type, is_nullable FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='external_profession_plans' "
            "AND column_name='idempotency_key'"
        ).fetchone() == ("character varying", "YES")
        if path == "production":
            assert connection.execute(
                "SELECT display_name, source_version FROM fiteatsy_client_directory WHERE id = %s",
                (sentinels["directory_id"],),
            ).fetchone() == ("Directory Sentinel", 7)
            assert connection.execute(
                "SELECT disposition FROM fiteatsy_client_directory_events WHERE event_id = %s",
                (sentinels["event_id"],),
            ).fetchone() == ("APPLIED",)
            assert connection.execute(
                "SELECT status FROM fiteatsy_client_directory_reconciliation_runs WHERE id = %s",
                (sentinels["reconciliation_id"],),
            ).fetchone() == ("COMPLETED",)
        plan_constraint = connection.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname = 'ck_external_profession_plan_status'"
        ).fetchone()[0]
        assert "REJECTED" in plan_constraint
        consent_fk = connection.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid = 'external_fiteatsy_consents'::regclass AND contype = 'f'"
        ).fetchone()[0]
        assert "external_fiteatsy_connections" in consent_fk
        assert "ON DELETE RESTRICT" in consent_fk
