#!/usr/bin/env python3
"""Read-only verification of the Practice Operations schema at migration 0064."""

import json
import os
import sys

import psycopg


EXPECTED_TABLES = {
    "fiteatsy_client_directory",
    "fiteatsy_client_directory_events",
    "fiteatsy_client_directory_reconciliation_runs",
    "external_practice_clients",
}
EXPECTED_COLUMNS = {
    "fiteatsy_client_directory": {
        "id", "fiteatsy_user_id", "fiteatsy_client_id", "display_name",
        "mobile_number_normalized", "email_normalized", "account_status",
        "mobile_verified", "registration_status", "registered_at",
        "source_updated_at", "source_version", "last_synced_at", "sync_status",
        "deleted_at", "created_at", "updated_at",
    },
    "fiteatsy_client_directory_events": {
        "event_id", "event_type", "fiteatsy_user_id", "source_version",
        "schema_version", "payload_sha256", "occurred_at", "processed_at",
        "disposition",
    },
    "fiteatsy_client_directory_reconciliation_runs": {
        "id", "started_at", "completed_at", "source_count", "destination_count",
        "missing_count", "stale_count", "duplicate_count", "status",
        "checkpoint_user_id", "error_code",
    },
    "external_profession_plans": {"idempotency_key"},
    "external_practice_clients": {
        "id", "tenant_id", "client_id", "first_name", "last_name", "email",
        "email_key", "mobile", "mobile_key", "status", "created_by",
        "idempotency_key", "created_at", "updated_at",
    },
}
EXPECTED_INDEXES = {
    "ix_fit_directory_mobile", "ix_fit_directory_registered",
    "ix_fit_directory_status", "ix_fit_directory_sync",
    "ix_fit_directory_event_user", "uq_external_diet_plan_creation_idempotency",
    "uq_external_practice_client_email", "uq_external_practice_client_mobile",
}
EXPECTED_CONSTRAINTS = {
    "ck_fit_directory_version", "ck_fit_directory_sync",
    "ck_fit_directory_registration", "ck_fit_directory_event_disposition",
    "ck_fit_directory_reconcile_status", "external_practice_clients_pkey",
    "external_practice_clients_tenant_id_client_id_key",
    "external_practice_clients_tenant_id_idempotency_key_key",
    "external_practice_clients_check", "external_practice_clients_status_check",
}


def main() -> int:
    url = os.environ.get("READONLY_DATABASE_URL")
    if not url:
        print("READONLY_DATABASE_URL is required", file=sys.stderr)
        return 2

    # Enforce read-only mode during connection startup, before the first query.
    with psycopg.connect(url, options="-c default_transaction_read_only=on") as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW transaction_read_only")
            if cur.fetchone()[0] != "on":
                raise RuntimeError("database session is not read-only")

            cur.execute("SELECT version_num FROM practice_operations_alembic_version")
            revisions = sorted(row[0] for row in cur.fetchall())

            cur.execute("""
                SELECT tablename, tableowner FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
            """)
            table_owners = dict(cur.fetchall())

            cur.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            columns = {}
            for table, name, data_type, nullable, default in cur.fetchall():
                columns.setdefault(table, {})[name] = {
                    "type": data_type, "nullable": nullable == "YES", "default": default
                }

            cur.execute("""
                SELECT indexname, tablename, indexdef FROM pg_catalog.pg_indexes
                WHERE schemaname = 'public'
            """)
            indexes = {name: {"table": table, "definition": definition}
                       for name, table, definition in cur.fetchall()}

            cur.execute("""
                SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
                       pg_get_constraintdef(pc.oid)
                FROM information_schema.table_constraints tc
                JOIN pg_catalog.pg_constraint pc ON pc.conname = tc.constraint_name
                JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.connamespace
                WHERE tc.table_schema = 'public' AND pn.nspname = 'public'
                ORDER BY tc.table_name, tc.constraint_name
            """)
            constraints = [
                {"table": t, "name": n, "type": k, "definition": d}
                for t, n, k, d in cur.fetchall()
                if t in EXPECTED_TABLES
            ]

    missing_tables = sorted(EXPECTED_TABLES - table_owners.keys())
    missing_columns = {
        table: sorted(names - columns.get(table, {}).keys())
        for table, names in EXPECTED_COLUMNS.items()
        if names - columns.get(table, {}).keys()
    }
    missing_indexes = sorted(EXPECTED_INDEXES - indexes.keys())
    constraint_names = {item["name"] for item in constraints}
    missing_constraints = sorted(EXPECTED_CONSTRAINTS - constraint_names)
    relevant_owners = {t: table_owners[t] for t in sorted(EXPECTED_TABLES) if t in table_owners}
    owner_mismatch = len(set(relevant_owners.values())) > 1
    result = {
        "session_read_only": True,
        "alembic_revisions": revisions,
        "expected_revision": "0064_external_practice_clients",
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "missing_indexes": missing_indexes,
        "missing_constraints": missing_constraints,
        "table_owners": relevant_owners,
        "owner_mismatch": owner_mismatch,
        "relevant_columns": {t: columns.get(t, {}) for t in sorted(EXPECTED_COLUMNS)},
        "relevant_indexes": {n: indexes[n] for n in sorted(EXPECTED_INDEXES) if n in indexes},
        "relevant_constraints": constraints,
    }
    result["matches_0064_inventory"] = (
        revisions == ["0064_external_practice_clients"]
        and not missing_tables and not missing_columns and not missing_indexes
        and not missing_constraints
        and not owner_mismatch
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["matches_0064_inventory"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
