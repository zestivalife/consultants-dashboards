# P0 Client Visibility and Diet-Chart Reliability Checkpoint

## Scope and evidence boundary

- Baseline: `953136c83a02bce6bfb0d4d3554a36da2b9dd584` on `codex/p0-role-workspace-routing`.
- Production freeze remains active. No deployment, production data mutation, credential change, or session invalidation was performed.
- `services/practice-operations-service/app/fiteatsy_connections.py` remains user-owned and unmodified by this increment.
- Source and local regression evidence is not counted as database-backed or browser E2E acceptance.

## Authoritative contracts

| Concern | Persisted authority | Enforcement |
|---|---|---|
| Authentication and platform role | Auth service user, role, JWT and permissions | Auth service and API Gateway |
| Internal organisation membership | Auth `organization_memberships` with active status | `/api/v1/auth/me` and workspace guard |
| External practice membership | Auth external-tenant membership represented by an active organisation membership | `/api/v1/auth/me`; gateway derives tenant headers |
| Practice role and permissions | `external_practice_role_profiles` | Practice Operations `_team_guard` |
| Client directory visibility | Active `external_client_team_assignments`; practice-wide access where explicitly granted | Practice Operations client directory |
| Fiteatsy health-data access | `external_fiteatsy_connections.state`, consent scopes and consent history | Connection-scoped APIs; assignment alone never grants health access |
| Diet-plan ownership | `external_profession_plans.authorised_consultant_id`, tenant and client | Practice Operations plan lookup |
| Senior review | Diet-plan state plus backend review role | Practice Operations review transition |
| Mobile delivery | Exact published connection publication/version | `external_fiteatsy_plan_publications`; only active DIET_PLANS consent is readable |

`workspaceAuthorities` is a projection of persisted Auth memberships and backend roles. It is not a new membership store. `resolutionPath=MEMBERSHIP` is required for tenant-scoped authority; `BACKEND_ROLE` is limited to explicit platform-level roles.

## Confirmed root causes and corrections

1. The deployed frontend still calls `GET /v1/external/clients`. The production Fiteatsy service returns `404 Cannot GET /v1/external/clients`.
2. The new Practice Operations directory originally selected from active connections. That incorrectly hid assigned clients before PIN connection and hid revoked consent rather than exposing a restricted directory state.
3. Client assignment and health-data consent are separate persisted contracts. The directory now returns active assignments with `ASSIGNED_CONNECTION_PENDING`, active consent with `CONNECTED_CONSENT_ACTIVE`, and inactive/revoked consent as restricted states. `healthDataAuthorized` is true only for an active connection.
4. Diet-plan publication previously did not require the existing Senior Consultant approval transition. Publication now fails with `DIET_PLAN_APPROVAL_REQUIRED` unless the current exact version is `APPROVED`; approved and published versions are immutable.
5. The authoring UI previously bypassed review. It now exposes submit, start review, request changes, exact-version approval, and approved-version publication actions.

## Client and diet-chart endpoint matrix

| Frontend operation | Effective route / owner | Contract and authority | Status |
|---|---|---|---|
| List consultant clients | `GET /api/gateway/api/v1/practice-operations/clients` → Gateway → Practice Operations | Auth `/me` tenant, practice permission, assignment/practice-wide visibility; `{clients,pagination,practiceWide}` | Implemented locally; not deployed |
| Create/read/update client and Client360 | `/api/fiteatsy/v1/external/clients...` → Next proxy → Fiteatsy | Bearer token; backend contract is outside this repository | Calls exist; production route-by-route implementation not proven |
| Timeline, documents, reports and biomarkers | `/api/fiteatsy/v1/external/clients/{id}/...` → Fiteatsy | Bearer plus client authority/consent expected | Calls exist; upstream implementation not provable from this repository |
| Connection invitations and intake | `/api/fiteatsy/v1/external/clients/{id}/invitations...`, `/v1/external/intake/...` | Bearer for consultant actions; token for intake | Calls exist; upstream-owned |
| Search governed common foods | `GET /api/fiteatsy/v1/external/clients/{id}/common-foods` | Fiteatsy catalogue and client authority | Used by current authoring UI; upstream-owned |
| Legacy external diet-plan calls | `/api/fiteatsy/v1/external/clients/{id}/diet-plan...` and `/diet-plans...` | Fiteatsy bearer authority | Legacy functions remain, but current Client360 authoring does not use them |
| List client Diet Plans | `GET /api/gateway/api/v1/practice-operations/clients/{id}/diet-plans` | Tenant, client, authorised consultant; senior roles can review | Implemented |
| Create plan draft | `POST .../practice-operations/diet-plans` | Tenant, consultant, client and DIET_PLAN capability | Implemented |
| Read exact plan/version history | `GET .../practice-operations/diet-plans/{id}` | Tenant and plan actor/reviewer scope | Implemented |
| Save new draft version | `PUT .../diet-plans/{id}/draft` | Expected version; immutable approved/published states | Implemented |
| Submit/review/approve | `POST .../diet-plans/{id}/review` | Expected exact version; senior/admin role for review actions | Implemented and wired in UI |
| Publish | `POST .../diet-plans/{id}/publish` | Exact current version must be approved; assessment/readiness/measurement lineage checks | Corrected locally; not deployed |
| Mobile published-plan retrieval | Practice Operations Fiteatsy connection routes backed by `external_fiteatsy_plan_publications` | Active connection, `DIET_PLANS` scope, `PUBLISHED` only | Implemented in repository; end-to-end QA not executed |
| DOCX download/version comparison | Legacy Fiteatsy external routes | External upstream | Calls exist; end-to-end status unverified |

## Production request trace (read-only, unauthenticated)

- Frontend: `https://consultant.nuetra.in` is served by Vercel.
- Current frontend deployment: commit `22d18b0dcec8a7d4e4733a2b2ff797865a1a1396`, deployment `dpl_BSnPnyqHyc2Dvw7pZbzjQzdjPFFv`.
- `GET /api/gateway/api/v1/practice-operations/clients?limit=1` reaches the Next.js gateway proxy and then Railway, returning the expected unauthenticated `401` with request IDs `fb5041a6-f854-492c-803a-7ca8708262a4` and `MyzBpcwjS56neS7LxtoGcA`.
- Direct production `GET https://fiteatsy-mobile-production.up.railway.app/v1/external/clients?limit=1` returns `404 Cannot GET /v1/external/clients`, Railway request ID `_qXBlsl8T02e7I8Djq4OvQ`.
- The screenshot therefore reflects the deployed old SHA and the confirmed missing Fiteatsy route, not the local Practice Operations correction.

## Verification status

- Practice Operations full suite: 344 passed.
- Frontend production build: passed.
- Database-backed integration against synthetic QA data: blocked; this workspace is linked only to production Railway and the freeze prohibits using it for mutation-based QA.
- Real authenticated browser QA: blocked; no approved non-production URL or synthetic QA credentials were supplied.
- Production deployment and authenticated verification: not performed and not authorised.

