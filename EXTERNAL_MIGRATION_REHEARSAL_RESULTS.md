# External migration rehearsal results

## Fixture

- Environment: `p0-db-recovery-20261022`
- PostgreSQL service: `d5ad975e-bd80-4e21-91bd-a3dd1670445e`
- Volume: `9d5c04b6-f328-4f27-bf48-c9539b456747`
- Disposable database: `mp004_external_rehearsal`
- Source schema: production schema-only dump; no production rows copied
- Canonical marker: `0049_global_search_activity`

The fixture has separate storage from production and receives no production application traffic.

## Results

- First run: PASS
  - `external_0050_contact_photo`
  - `external_0051_multi_diet_plans`
  - `external_0053_client_profile`
  - `external_0054_nutrition_foundation`
- Second run: PASS, no migrations applied
- External ledger rows: 4
- Expected new External tables: 9/9 present
- Canonical Alembic head after rehearsal: `0049_global_search_activity`
- `internal_client_profile_enrichments`: absent
- Production data copied: none
- Production database modified: no

Automated migration and Phase 2A tests: 25/25 PASS.

## Failure behavior

Unit coverage proves fail-closed behavior for wrong canonical head and checksum drift. The runner wraps advisory lock, preconditions, DDL, and ledger writes in one database transaction; PostgreSQL therefore rolls back the set on any statement failure.

