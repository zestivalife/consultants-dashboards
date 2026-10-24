# Phase 2A release recovery plan

## Current decision

Phase 2A remains halted. No production migration or deployment is authorised.

## Recovery sequence

1. Obtain Railway-supported isolated snapshot restore or provider-assisted volume clone for backup `2efe8063-560c-4516-a27e-d99bffa6663a`.
2. Restore `82915095-50f8-4b6f-83f8-06ead0b26266` into a second independently verified service.
3. Confirm both service IDs and volume IDs differ from production service `e800ac1e-d873-4717-b7dc-807696c97012` and volume `1a692ebd-6b8c-41fa-9b97-1866124971d2`.
4. Apply no application traffic or production credentials to either service.
5. Run deterministic record-level comparison and reconcile Window A.
6. Select the authoritative database based on evidence.
7. If cutover is required, request specific informed approval for service/volume IDs, write quiescence, downtime, and rollback.
8. After recovery acceptance, run the External-only migration against a fresh authoritative clone.
9. Re-run regression and exact-SHA CI for the final source candidate.
10. Request a separate Phase 2A production release approval.

## Recommended database action

Keep production unchanged until parity is established. No volume label, creation time, or database size is sufficient to choose an authoritative state.

## Cutover controls

- block mutation routes while retaining read-only health endpoints;
- capture a fresh backup after quiescence;
- verify active connection drain;
- attach only the approved destination volume;
- verify migration head, stable hashes, identities, clinical records, and tenant isolation;
- retain the previous volume and recovery backup for rollback;
- reopen writes only after integrity checks pass.

Expected downtime is limited to the approved quiescence/cutover window; no downtime is required for isolated comparison.
