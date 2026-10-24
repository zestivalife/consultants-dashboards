"""Transactional External-only migration runner.

This runner intentionally does not write ``practice_operations_alembic_version``.
It is valid only for the audited production baseline at canonical revision 0049.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

import psycopg

CANONICAL_BASELINE = "0049_global_search_activity"
LEDGER_TABLE = "external_practice_schema_migrations"
ADVISORY_LOCK_KEY = 90490054


@dataclass(frozen=True)
class ExternalMigration:
    migration_id: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n-- statement --\n".join(statement.strip() for statement in self.statements)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


MIGRATIONS: tuple[ExternalMigration, ...] = (
    ExternalMigration("external_0050_contact_photo", (
        """CREATE TABLE IF NOT EXISTS external_consultant_contact_profiles(
          id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, consultant_user_id VARCHAR(120) NOT NULL,
          country_iso2 VARCHAR(2) NOT NULL, country_code VARCHAR(5) NOT NULL, national_number VARCHAR(20) NOT NULL,
          phone_e164 VARCHAR(16) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
          CONSTRAINT uq_external_consultant_contact UNIQUE(tenant_id,consultant_user_id),
          CONSTRAINT ck_external_phone_e164 CHECK(phone_e164 ~ '^\\+[1-9][0-9]{7,14}$'))""",
        """CREATE TABLE IF NOT EXISTS external_consultant_profile_photos(
          id UUID PRIMARY KEY, profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id) ON DELETE RESTRICT,
          tenant_id VARCHAR(80) NOT NULL, object_key TEXT NOT NULL, filename VARCHAR(255) NOT NULL,
          content_type VARCHAR(40) NOT NULL, size_bytes BIGINT NOT NULL, status VARCHAR(24) NOT NULL,
          created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, uploaded_at TIMESTAMPTZ, replaced_at TIMESTAMPTZ,
          CONSTRAINT uq_external_profile_photo_object UNIQUE(tenant_id,object_key),
          CONSTRAINT ck_external_profile_photo_status CHECK(status IN ('PENDING_UPLOAD','AVAILABLE','UPLOAD_FAILED','REPLACED')),
          CONSTRAINT ck_external_profile_photo_size CHECK(size_bytes > 0 AND size_bytes <= 5242880))""",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_external_profile_current_photo ON external_consultant_profile_photos(profile_id) WHERE status='AVAILABLE' AND replaced_at IS NULL",
    )),
    ExternalMigration("external_0051_multi_diet_plans", (
        "ALTER TABLE external_profession_plans ADD COLUMN IF NOT EXISTS daily_calories_target INTEGER",
        "ALTER TABLE external_profession_plans ADD COLUMN IF NOT EXISTS daily_protein_target_g NUMERIC(8,2)",
        "ALTER TABLE external_profession_plans ADD COLUMN IF NOT EXISTS authorised_consultant_id VARCHAR(120)",
        "ALTER TABLE external_profession_plan_versions ADD COLUMN IF NOT EXISTS nutrition_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb",
        "ALTER TABLE external_profession_plans DROP CONSTRAINT IF EXISTS ck_external_profession_plan_status",
        "ALTER TABLE external_profession_plans ADD CONSTRAINT ck_external_profession_plan_status CHECK (status IN ('DRAFT','SAVED','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED','APPROVED','PUBLISHED','SUPERSEDED','ARCHIVED'))",
        "ALTER TABLE external_profession_plan_versions DROP CONSTRAINT IF EXISTS ck_external_profession_plan_version_status",
        "ALTER TABLE external_profession_plan_versions ADD CONSTRAINT ck_external_profession_plan_version_status CHECK (status IN ('DRAFT','SAVED','SUBMITTED','UNDER_REVIEW','CHANGES_REQUESTED','APPROVED','PUBLISHED','SUPERSEDED'))",
        "CREATE INDEX IF NOT EXISTS ix_external_diet_plans_scope ON external_profession_plans(tenant_id,client_id,updated_at DESC) WHERE plan_type='DIET_PLAN'",
    )),
    ExternalMigration("external_0053_client_profile", (
        """CREATE TABLE IF NOT EXISTS external_client_profile_enrichments (
          tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
          values JSONB NOT NULL DEFAULT '{}'::jsonb, version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
          schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version > 0),
          provenance JSONB NOT NULL DEFAULT '{}'::jsonb, audit_history JSONB NOT NULL DEFAULT '[]'::jsonb,
          created_by VARCHAR(120) NOT NULL, updated_by VARCHAR(120) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
          PRIMARY KEY (tenant_id, client_id), CHECK (jsonb_typeof(values) = 'object'),
          CHECK (jsonb_typeof(provenance) = 'object'), CHECK (jsonb_typeof(audit_history) = 'array'))""",
        "CREATE INDEX IF NOT EXISTS ix_external_client_profile_updated ON external_client_profile_enrichments(tenant_id, updated_at DESC)",
    )),
    ExternalMigration("external_0054_nutrition_foundation", (
        """CREATE TABLE IF NOT EXISTS external_nutrition_assessments (
          id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
          authorised_consultant_id VARCHAR(120) NOT NULL, status VARCHAR(30) NOT NULL,
          current_version INTEGER NOT NULL CHECK(current_version > 0), review_state VARCHAR(30) NOT NULL,
          consent_state VARCHAR(30) NOT NULL, stale BOOLEAN NOT NULL DEFAULT FALSE, stale_reason TEXT,
          created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
          CONSTRAINT ck_external_nutrition_assessment_status CHECK(status IN ('DRAFT','IN_REVIEW','APPROVED','CHANGES_REQUESTED')),
          CONSTRAINT ck_external_nutrition_review_state CHECK(review_state IN ('NOT_REVIEWED','IN_REVIEW','REVIEWED','CHANGES_REQUESTED')),
          CONSTRAINT uq_external_nutrition_assessment_version UNIQUE(id,current_version))""",
        "CREATE INDEX IF NOT EXISTS ix_external_nutrition_assessment_client ON external_nutrition_assessments(tenant_id,client_id,updated_at DESC)",
        """CREATE TABLE IF NOT EXISTS external_nutrition_assessment_versions (
          id UUID PRIMARY KEY, assessment_id UUID NOT NULL REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT,
          tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, version INTEGER NOT NULL,
          source_manifest JSONB NOT NULL, calculation_methodologies JSONB NOT NULL, calculations JSONB NOT NULL,
          input_completeness JSONB NOT NULL, clinical_safety_findings JSONB NOT NULL,
          nutrition_considerations JSONB NOT NULL, provenance JSONB NOT NULL,
          fingerprint_sha256 VARCHAR(64) NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
          reviewed_by VARCHAR(120), reviewed_at TIMESTAMPTZ,
          CONSTRAINT uq_external_nutrition_assessment_version_row UNIQUE(assessment_id,version),
          CONSTRAINT uq_external_nutrition_assessment_fingerprint UNIQUE(tenant_id,client_id,fingerprint_sha256),
          CHECK(jsonb_typeof(source_manifest)='array'), CHECK(jsonb_typeof(calculations)='object'))""",
        "CREATE INDEX IF NOT EXISTS ix_external_nutrition_version_client ON external_nutrition_assessment_versions(tenant_id,client_id,created_at DESC)",
        """CREATE TABLE IF NOT EXISTS external_nutrition_assessment_inputs (
          id UUID PRIMARY KEY, assessment_version_id UUID NOT NULL REFERENCES external_nutrition_assessment_versions(id) ON DELETE RESTRICT,
          tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, source_type VARCHAR(60) NOT NULL,
          source_id VARCHAR(160) NOT NULL, source_version VARCHAR(120) NOT NULL, source_status VARCHAR(40) NOT NULL,
          observed_at TIMESTAMPTZ, provenance JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL,
          UNIQUE(assessment_version_id,source_type,source_id,source_version))""",
        "CREATE INDEX IF NOT EXISTS ix_external_nutrition_input_source ON external_nutrition_assessment_inputs(tenant_id,client_id,source_type,source_id)",
        """CREATE TABLE IF NOT EXISTS external_diet_plan_assessment_links (
          id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
          external_plan_id VARCHAR(160) NOT NULL, external_plan_version VARCHAR(120) NOT NULL,
          assessment_id UUID REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT,
          assessment_version INTEGER, source_fingerprint_sha256 VARCHAR(64), calculation_methodologies JSONB NOT NULL DEFAULT '{}'::jsonb,
          plan_state VARCHAR(30) NOT NULL, legacy_lineage_state VARCHAR(40) NOT NULL DEFAULT 'LINKED',
          created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
          UNIQUE(tenant_id,client_id,external_plan_id,external_plan_version),
          CHECK((legacy_lineage_state='LEGACY_UNAVAILABLE' AND assessment_id IS NULL) OR (legacy_lineage_state='LINKED' AND assessment_id IS NOT NULL)))""",
        "CREATE INDEX IF NOT EXISTS ix_external_plan_assessment ON external_diet_plan_assessment_links(tenant_id,client_id,assessment_id)",
        """CREATE TABLE IF NOT EXISTS external_clinical_document_links (
          id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
          document_reference VARCHAR(240) NOT NULL, health_record_reference VARCHAR(240), extraction_run_reference VARCHAR(240),
          observation_references JSONB NOT NULL DEFAULT '[]'::jsonb, source_available BOOLEAN NOT NULL,
          source_status VARCHAR(40) NOT NULL, created_by VARCHAR(120) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
          UNIQUE(tenant_id,client_id,document_reference), CHECK(jsonb_typeof(observation_references)='array'),
          CHECK((source_available AND source_status='AVAILABLE') OR (NOT source_available AND source_status IN ('HISTORICAL_SOURCE_UNAVAILABLE','QUARANTINED'))))""",
        """CREATE TABLE IF NOT EXISTS external_nutrition_staleness_events (
          id UUID PRIMARY KEY, assessment_id UUID NOT NULL REFERENCES external_nutrition_assessments(id) ON DELETE RESTRICT,
          tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, source_type VARCHAR(60) NOT NULL,
          source_id VARCHAR(160) NOT NULL, source_version VARCHAR(120) NOT NULL, reason TEXT NOT NULL,
          resolved_at TIMESTAMPTZ, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL)""",
        "CREATE INDEX IF NOT EXISTS ix_external_nutrition_stale_client ON external_nutrition_staleness_events(tenant_id,client_id,created_at DESC)",
    )),
    ExternalMigration("external_0055_client_measurements", (
        """CREATE TABLE IF NOT EXISTS external_client_measurements (
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
                                  (version>1 AND supersedes_id IS NOT NULL AND length(correction_reason)>=3)))""",
        "CREATE INDEX IF NOT EXISTS ix_external_client_measurements_latest ON external_client_measurements(tenant_id,client_id,measurement_type,measured_at DESC,version DESC)",
        "CREATE INDEX IF NOT EXISTS ix_external_client_measurements_series ON external_client_measurements(tenant_id,client_id,series_id,version DESC)",
    )),
)

PRECONDITIONS = {
    "external_0050_contact_photo": """SELECT
      to_regclass('public.external_consultant_contact_profiles') IS NULL AND
      to_regclass('public.external_consultant_profile_photos') IS NULL""",
    "external_0051_multi_diet_plans": """SELECT NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND
        ((table_name='external_profession_plans' AND column_name IN
          ('daily_calories_target','daily_protein_target_g','authorised_consultant_id')) OR
         (table_name='external_profession_plan_versions' AND column_name='nutrition_snapshot')))""",
    "external_0053_client_profile": "SELECT to_regclass('public.external_client_profile_enrichments') IS NULL",
    "external_0054_nutrition_foundation": """SELECT NOT EXISTS (
      SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name IN
      ('external_nutrition_assessments','external_nutrition_assessment_versions',
       'external_nutrition_assessment_inputs','external_diet_plan_assessment_links',
       'external_clinical_document_links','external_nutrition_staleness_events'))""",
    "external_0055_client_measurements": "SELECT to_regclass('public.external_client_measurements') IS NULL",
}


def _verify_baseline(cursor) -> None:
    cursor.execute("SELECT version_num FROM practice_operations_alembic_version")
    rows = cursor.fetchall()
    if rows != [(CANONICAL_BASELINE,)]:
        raise RuntimeError(f"canonical migration baseline must be exactly {CANONICAL_BASELINE}; found {rows!r}")


def _ensure_ledger(cursor) -> None:
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {LEDGER_TABLE}(
      migration_id VARCHAR(120) PRIMARY KEY,
      checksum_sha256 VARCHAR(64) NOT NULL,
      applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CHECK(length(checksum_sha256)=64))""")


def apply_external_migrations(connection, migrations: Iterable[ExternalMigration] = MIGRATIONS) -> list[str]:
    """Apply pending External migrations atomically and return their IDs."""
    applied: list[str] = []
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (ADVISORY_LOCK_KEY,))
            _verify_baseline(cursor)
            _ensure_ledger(cursor)
            cursor.execute(f"SELECT migration_id, checksum_sha256 FROM {LEDGER_TABLE}")
            recorded = dict(cursor.fetchall())
            for migration in migrations:
                existing = recorded.get(migration.migration_id)
                if existing:
                    if existing != migration.checksum:
                        raise RuntimeError(f"checksum mismatch for {migration.migration_id}")
                    continue
                cursor.execute(PRECONDITIONS[migration.migration_id])
                if cursor.fetchone() != (True,):
                    raise RuntimeError(
                        f"untracked or partially applied schema detected for {migration.migration_id}"
                    )
                for statement in migration.statements:
                    if "internal_" in statement.lower():
                        raise RuntimeError(f"Internal schema reference rejected in {migration.migration_id}")
                    cursor.execute(statement)
                cursor.execute(
                    f"INSERT INTO {LEDGER_TABLE}(migration_id,checksum_sha256) VALUES (%s,%s)",
                    (migration.migration_id, migration.checksum),
                )
                applied.append(migration.migration_id)
    return applied


def run(database_url: str) -> list[str]:
    with psycopg.connect(database_url) as connection:
        return apply_external_migrations(connection)
