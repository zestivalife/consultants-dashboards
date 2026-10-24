# External-only migration design

## Problem

The canonical Alembic chain is:

`0049 -> 0050 External -> 0051 External -> 0052 Internal -> 0053 External -> 0054 External`

`0053` and `0054` have only revision-order dependencies on `0052`; their SQL has no table, foreign-key, function, or data dependency on `internal_client_profile_enrichments`. Executing the canonical chain would nevertheless create an Internal table and violate the freeze.

## Design

The External schema uses a governed runner at:

- `services/practice-operations-service/external_migrations/runner.py`
- `services/practice-operations-service/external_migrations/__main__.py`

It applies only the SQL effects of canonical migrations 0050, 0051, 0053, and 0054. Historical Alembic files are unchanged.

Safety properties:

- requires canonical head to be exactly `0049_global_search_activity`;
- never writes `practice_operations_alembic_version`;
- records immutable SHA-256 checksums in `external_practice_schema_migrations`;
- takes a transaction-scoped PostgreSQL advisory lock;
- applies the complete External set in one transaction;
- detects untracked or partially applied target objects and fails closed;
- rejects any migration statement containing `internal_`;
- contains no destructive backfill, delete, truncate, or drop-table operation;
- repeated execution verifies checksums and performs no DDL;
- canonical migration head remains unambiguous at 0049.

## Ownership and future convergence

The canonical and External ledgers represent separate governed domains:

- `practice_operations_alembic_version`: frozen canonical/Internal lineage;
- `external_practice_schema_migrations`: External-only schema lineage.

Future migrations must explicitly declare their ledger. Canonical Alembic must not be advanced through historical 0050–0054 on a database carrying the External ledger, because that would duplicate objects and execute 0052. If the Internal freeze is later reopened, a new reconciliation revision must inspect the External ledger, validate object checksums, create only the separately authorised Internal objects, and record a reviewed convergence marker. Historical migrations must remain unchanged and must not be blindly stamped.

## Operational command

The runner is invoked only after recovery acceptance:

`python -m external_migrations`

It requires `DATABASE_URL` and prints migration identifiers only, never credentials or row data.

