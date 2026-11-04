# Production engineering baseline — 2026-11-04

Status: verified recovery baseline; authenticated end-to-end acceptance remains open.

## Immutable deployment inventory

| Service | Source provenance | Railway deployment | Image digest | Runtime gate |
|---|---|---|---|---|
| Assessment | `0edaabfa992991653c718b74b6025a7dbda92b64` | `74db2929-f22b-4751-9d89-18cccec2774b` | `sha256:1a023243be8209d342365f930d9b57aa1486c44c66973624f0b65040c392b073` | health 200; readiness 200; database and Redis OK |
| Nutrition | `1c10d1694681cb18938db26dc283c0f39b6b3108` | `1867575b-27f6-4835-ad4c-6136fe344272` | `sha256:49239e0a8afa7d84b3c5695a617341e4fefc5223b58880768a22ca68b01c3cca` | health 200; readiness 200; database and Redis OK |
| Scoring | `f2629d282920fa0fc45fc5d89e8531d378432398` | `5771634b-c5e4-416e-9057-7300d4597703` | `sha256:a9935bd495c1452ddb6de61d2bf3e0ba39c5d5ae4e86b4c811057589ef2795ff` | health 200; readiness 200; database and Redis OK |
| Fiteatsy backend | clean source archive at `f7762c1eed4c3026913028742655d6c3f5a6e38e` | `4327986d-1bad-47e8-ace8-ab8b23af7d1a` | `sha256:2ebb1aa688a140d98d0c3e145c26ec12cac93e3fdf35a2b61907e6d06d2791a6` | health 200; readiness 200; database ready |

Railway projects and environments:

- Consultant platform: project `a8bd7357-120a-4e99-8682-2051488b2d28`, environment `production`.
- Fiteatsy: project `8ba18169-e239-4925-9009-f53f62c6c508`, environment `production`.

The Fiteatsy `/v1/version` response currently reads a stale `GIT_COMMIT` environment value. The deployment ID, clean-source archive and image digest are the current provenance evidence. Runtime commit metadata is not authoritative until this gap is repaired and tested.

## Database baseline

| Owner | Version table | Production revision |
|---|---|---|
| Auth | `alembic_version` | `d8e9f0a1b2c3` |
| Assessment | `assessment_service_alembic_version` | `0001` |
| Nutrition | `nutrition_service_alembic_version` | `0001` |
| Practice Operations | `practice_operations_alembic_version` | `0064_external_practice_clients` |
| Profile | `profile_service_alembic_version` | `dddea0ba61fa` |
| Scoring | `scoring_engine_service_alembic_version` | `0003` |

The version tables are service-specific except Auth's established table. No framework work may stamp, reset or mutate production migration history.

## Protected state

- The primary Fiteatsy worktree contains extensive uncommitted mobile, backend and generated-output work and must not be used for reliability edits.
- The primary Consultant worktree contains protected `services/practice-operations-service/app/fiteatsy_connections.py` changes.
- Reliability changes are developed only in clean isolated worktrees.
- Production food catalogue counts and digests are recorded in the recovery evidence and must remain unchanged.
- Super Admin authority, tenant memberships, credentials, PINs, consent and user records are protected.

## Existing automated controls

- Consultant exact-SHA workflow: `.github/workflows/frontend-exact-sha-ci.yml`.
- Consultant regression coverage: Practice Operations, database-backed plan/client contracts, Auth authority, Gateway, frontend tests and production build.
- Fiteatsy workflows: `.github/workflows/consultant-database-l3.yml`, `.github/workflows/nutrition-catalogue-envc.yml`, `.github/workflows/frozen-splash-contract.yml`.
- Fiteatsy API and database suites live under `tests/api`, `tests/backend` and `tests/database`.

## Known release gaps

1. No authenticated production External Consultant → Fiteatsy E2E evidence exists for this baseline.
2. Fiteatsy runtime commit metadata is stale.
3. Railway CLI uploads rebuild images; immutable staging-to-production image promotion is not yet enforced.
4. The Fiteatsy Railway Dockerfile path and repository build context are incompatible without special packaging.
5. Assessment, Nutrition and Scoring previously allowed an undeclared `db_pool_timeout` to reach production; the three deployed fixes are consolidated on the reliability branch with regression tests.
6. A Railway `SUCCESS` state is insufficient without health, readiness, authentication and functional contract gates.

## Change boundary

This document records evidence; it does not authorize deployment or production mutation. Production changes require explicit approval. Full acceptance remains blocked until deterministic synthetic authenticated staging workflows execute across real services and databases.
