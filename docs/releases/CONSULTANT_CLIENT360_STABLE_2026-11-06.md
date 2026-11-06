# Consultant Client 360 stable baseline — 2026-11-06

Status: `PRODUCTION VERIFIED`

Immutable tag: `consultant-client360-stable-2026-11-06`

This manifest records the production identities observed on 2026-11-06. An unavailable Git SHA is recorded as unknown; deployment IDs and image digests are not converted into inferred source identities.

## Serving identities

| Surface | Source identity | Deployment identity | Immutable artifact / runtime evidence |
| --- | --- | --- | --- |
| Consultant frontend | `77d52cc733cf878516f99dae74e52f964efd7ac4` | `dpl_DudxeH2mwrrU1nuoYY1qXJwzGBgZ` | `/api/version`, browser bundle and production alias agree |
| Fiteatsy backend | runtime reports `6ab7c51c82c7977d21ebed03fd29b7d7bbd73a12` | `fd569e19-7d74-438d-871e-dd62f9196405` | `sha256:f6bcc489178ddc49abfa34bb47c92ae4022d0d6e846ccac7a863eeda691a7604`; `/health` and `/ready` pass |
| Practice Operations | deployment message identifies `47d429689d85b90b5cbb6cc90e4eef033ba0c8f9` | `9624603c-9f78-4368-9c3d-6e75153a16a2` | `sha256:9560af4dc871e2faf88a3c87249fa77a4dae589087b6cf42499fec554ed6c990`; Gateway readiness reports upstream `ok` |
| API Gateway | `1fbcd662602a20ead0eb9b188002f9604f7623ca` | `9dd675bc-e324-472d-95c6-a09364c4ec6c` | `sha256:bcfb540b586d99352fa58207f12e15919e0f844377062d387ed589c5174c67b7`; readiness is degraded because Assessment, Nutrition and Scoring internal checks are unavailable |
| Auth | `ca23ca3802f66371fc15a1fce6d4a2ccd7db2190` | `f04daeb4-3e55-4024-8f6c-2abf03c58a4f` | `sha256:7b7d3d09810c71a1dc28fba31db8a28ede6c68f2b3e64766048f289345cb8878`; ready |
| Profile | unknown | `30c98900-f36d-422e-817c-87846bb82a1c` | `sha256:f0efb15e74b4e5ce68f938ddb50b35221d2558751b3dea44b9265fb3389abac3`; ready |
| Assessment | deployment label `0edaabf` (full runtime SHA unavailable) | `74db2929-f22b-4751-9d89-18cccec2774b` | `sha256:1a023243be8209d342365f930d9b57aa1486c44c66973624f0b65040c392b073`; direct readiness passes |
| Nutrition | deployment label `1c10d16` (full runtime SHA unavailable) | `1867575b-27f6-4835-ad4c-6136fe344272` | `sha256:49239e0a8afa7d84b3c5695a617341e4fefc5223b58880768a22ca68b01c3cca`; direct readiness passes |
| Scoring | deployment label `f2629d2` (full runtime SHA unavailable) | `5771634b-c5e4-416e-9057-7300d4597703` | `sha256:a9935bd495c1452ddb6de61d2bf3e0ba39c5d5ae4e86b4c811057589ef2795ff`; direct readiness passes |

## Migration evidence

- Auth readiness reports revision `d8e9f0a1b2c3`.
- Practice Operations production revision previously verified as `0064_external_practice_clients`; the current readiness surface does not expose it, so it is preserved as prior verified evidence rather than a fresh runtime claim.
- Profile, Assessment, Nutrition and Scoring readiness currently report migration identity as unknown. Their database checks pass; no production migration operation was performed.

## Protected contracts

- Session restoration and secure-update identity agreement: browser bundle SHA equals `/api/version` SHA.
- Tenant-scoped roster and assignment visibility through the existing workspace loader.
- Connected Client 360 health data through `GET /api/v1/practice-operations/fiteatsy-connections/{connection_id}/health-context`.
- Profile enrichment and measurements through tenant-scoped Practice Operations client routes.
- Connection, assignment and consent remain distinct; no synthetic connection identifier is permitted.
- Diet lifecycle remains Practice Operations-owned: list/create, draft save, exact-version review, publish and active Fiteatsy plan retrieval.

## Mandatory regression gates

The following production checks passed on the tagged frontend and must remain release-blocking:

1. Existing consultant session restores and secure-update verification passes.
2. Dashboard loads.
3. Client roster loads exactly Rest fit and Kirti for the authorised practice.
4. Rest fit Client 360 opens without a client-side exception.
5. Basic profile, assessment projection and food preference render.
6. Delegated health context renders with consent enforcement.
7. Measurements and biomarkers render honest unavailable/empty states.
8. Diet Plans navigation and generation entry load.
9. Leads continues to load.
10. Cross-tenant, unconnected, revoked and expired consent paths remain fail-closed in automated regression coverage.

Exact-SHA CI: [run 42106578770](https://github.com/zestivalife/consultants-dashboards/actions/runs/42106578770), `success`, exact SHA `77d52cc733cf878516f99dae74e52f964efd7ac4`.

## Known unfinished work

- Health Profile evidence-review call returns HTTP 404 for `GET /api/fiteatsy/v1/external/clients/{client_id}/profile-evidence-reviews`; this is not an Idempotency-Key failure and does not invalidate the loaded Client 360 projection.
- Rest fit Nutrition Assessment is `NOT STARTED`.
- Diet generation, draft persistence/reopen, exact-version self-approval, publication and Fiteatsy mobile Nutrition retrieval have not been production-accepted.
- Write verification requires an authorised synthetic client and reviewed test plan; Rest fit and Kirti must not be mutated for acceptance testing.

## Preservation boundary

Do not alter Auth, membership, roster, Gateway, Practice Operations assignment/consent logic, Client 360 projections, Super Admin, Indian Common Food, completed migrations, or protected uncommitted work as part of follow-on diet workflow changes.
