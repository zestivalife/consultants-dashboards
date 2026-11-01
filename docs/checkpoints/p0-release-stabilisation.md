# P0 release stabilisation checkpoint

Baseline: `79413780b11a2111037d84cb7cdb1b8eb16ba557`
Branch: `codex/p0-role-workspace-routing`

## Frontend failure disposition (original 16)

| # | Test and assertion | Expected / actual | Governing contract | Disposition and corrective action |
|---|---|---|---|---|
| 1 | `client-specific-dietchart-biomarker-repair.test.mjs` — `getExternalDietPlan(client.id)` | Legacy single-plan fetch / `ExternalMultiDietPlan` | Practice Operations owns versioned Diet Plans | Obsolete assertion; assert the governed multi-plan component. |
| 2 | `common-food-ui.test.mjs` — consultant client route | `/v1/consultants/clients/{id}` / `/v1/external/clients/{id}` | External tenant common-food calls remain on the gateway external authority route | Obsolete assertion; assert `/v1/external/clients/{id}`. The same test exposed a defective random idempotency fallback; replace `Math.random()` with `crypto.randomUUID()`. |
| 3 | `external-client360-data-repair.test.mjs` — Diet Plan actions | Four legacy action labels / `Open Diet Plans` | Client 360 opens the governed plan workspace | Obsolete assertion; assert the current action and `ExternalMultiDietPlan`. |
| 4 | `external-client360-data-repair.test.mjs` — authoring context | Context rendered in Client 360 / split between Client 360 and multi-plan editor | Context remains read-only; publication is approval-gated | Obsolete location assertion; inspect both components and assert approved publication. |
| 5 | `external-client360-route-mount.test.mjs` — legacy consultant route | Direct external workspace mount / authenticated `LegacyWorkspaceRedirect` | Legacy URLs redirect only after `/auth/me` workspace resolution | Obsolete assertion; assert the safe redirect. |
| 6 | `external-diet-plan.test.mjs` — Client 360 plan contract | Legacy `getExternalDietPlan` / governed multi-plan workspace | Versioned Practice Operations plan contract | Obsolete assertion; assert `ExternalMultiDietPlan`. |
| 7 | `external-diet-plan.test.mjs` — persistence | legacy generate/draft route / Practice Operations versioned draft API | Immutable versions use `expected_version` | Obsolete assertion; assert `saveConsultantDietPlan` and the versioned endpoint. |
| 8 | `external-diet-plan.test.mjs` — card data | legacy option validators / backend nutrition snapshot | Plan history renders persisted snapshots | Obsolete assertion; assert the backend snapshot and no placeholder nutrition. |
| 9 | `external-diet-plan.test.mjs` — publication | consultant self-publish / submit, Senior approval, then publish | Exact-version Senior approval is mandatory | Obsolete and unsafe assertion; assert submit/approve/publish with `expected_version`. |
| 10 | `external-diet-plan.test.mjs` — DOCX | legacy external client download / no current endpoint | DOCX must be generated from the governed current version | Implementation defect; add Practice Operations download endpoint, frontend API adapter and button. |
| 11 | `external-diet-plan.test.mjs` — common-food editor | editor embedded in Client 360 / editor embedded in multi-plan workspace | Shared editor remains injected through an external-authority adapter | Obsolete location assertion; assert adapter operations in `ExternalMultiDietPlan`. |
| 12 | `external-focused-missing-information.test.mjs` — nutrition target validation | validation in Client 360 / validation in plan creation form | 800–6000 kcal and 20–400 g protein bounds | Obsolete location assertion; assert the active form validation. |
| 13 | `external-health-records-communication.test.mjs` — plan component | `ExternalDietPlan` / `ExternalMultiDietPlan` | Current governed multi-plan component | Obsolete assertion; update component name. |
| 14 | `external-health-records-communication.test.mjs` — plan sharing | self-published plan / approved exact version before publication | Consultants cannot bypass Senior review | Obsolete and unsafe assertion; assert approved-only publication and no fabricated delivery events. |
| 15 | `external-saas-p0-foundation.test.mjs` — legacy route | direct workspace mount / authorised legacy redirect | Canonical `/workspace/external-consultant/*` routing | Obsolete assertion; assert `LegacyWorkspaceRedirect`. |
| 16 | `food-authorisation-ui.test.mjs` — owner default | `/dashboard/owner` / canonical super-admin workspace | Role-specific canonical workspace routes | Obsolete assertion; assert `CANONICAL_WORKSPACE_PATHS['super-admin']`. |

Result: `node --test tests/*.test.mjs` — **553 passed, 0 failed**.

## PostgreSQL-backed contracts

- Added migrations for the runtime-required `external_client_measurements` table and explicit Diet Plan `REJECTED` state.
- Client directory real HTTP/SQL test covers unauthenticated, wrong tenant type, inactive practitioner, assignment-only, active consent, revoked consent, inactive connection, duplicate assignments, removed/unassigned clients, practice-wide union, pagination/total and cross-tenant isolation.
- Assignment alone exposes no email/profile or health data. Active scoped consent is required.
- Auth `/api/v1/auth/me` real HTTP/SQL test confirms: internal and Senior authority comes from active `organization_memberships`; external authority comes from active `external_signup_provisioning`; Super Admin comes from an explicit backend role; inactive membership yields no workspace authority.
- Diet Plan real HTTP/SQL test covers immutable versions, submit, changes requested, rejection, simultaneous edit/stale approval, exact-version approval, unauthorised actor, idempotent publication, deterministic DOCX, exact published content, mobile retrieval and revoked consent.

## Safety and remaining acceptance

- Production was not accessed or mutated.
- The pre-existing `services/practice-operations-service/app/fiteatsy_connections.py` modification is excluded from this work. Required diff checksum: `2263d12287ce70cb4a3de66b2edb00642be8bff5dc58e6753e92c99da61367c7`.
- Authenticated browser checks with approved real QA identities remain blocked until QA identity credentials/environment access are supplied.
- Release remains blocked until the final exact SHA completes the GitHub Actions workflow successfully.
