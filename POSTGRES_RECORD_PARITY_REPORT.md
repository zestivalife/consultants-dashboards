# PostgreSQL record parity report

## Decision

`DATA_PARITY_UNVERIFIED`

The pre-incident and incident-state backups have not been mounted into two independently verified services, so record-level parity cannot yet be truthfully asserted.

## Available comparison evidence

The currently attached state has no detected Window B tuple mutations. An older isolated recovery environment (`p0-db-recovery-20261022`, service `d5ad975e-bd80-4e21-91bd-a3dd1670445e`, volume `9d5c04b6-f328-4f27-bf48-c9539b456747`) was inspected only for lineage context. It is not a substitute for the original production snapshot.

Privacy-preserving set hashes showed:

| Dataset | Current attached | Older isolated recovery | Classification |
|---|---:|---:|---|
| Users | 65 | 65 | Stable identifiers identical; row values not identical |
| User roles | 72 | 73 | Different |
| Auth audit history | 2,079 | 2,109 | Different |

The older recovery environment has migration head `0051_multi_diet_plans`; the current production database is at `0049_global_search_activity`. These differences confirm the older environment is a separate lineage and cannot establish production parity.

## Required deterministic comparison

Once both preserved backups are restored to isolated services, compare every in-scope table using:

1. schema/type/constraint/index fingerprints;
2. stable primary-key sets;
3. canonical row hashes with explicit type tags for NULL, numeric, timestamp, byte, array, object, and string values;
4. version and created/updated timestamps;
5. foreign-key integrity and orphan counts;
6. ordered audit-event sequences.

Sensitive row-level evidence must remain in restricted storage. Reports should contain counts, keyed hashes, classifications, and redacted identifiers only.

## Current classification

- Identity parity: unverified
- Clinical parity: unverified
- Diet Plan parity: unverified
- Audit-history parity: unverified
- Window A: no write evidence, but unverified
- Window B: no detected logical writes
- Original detached volume: preserved, not safely inspected

