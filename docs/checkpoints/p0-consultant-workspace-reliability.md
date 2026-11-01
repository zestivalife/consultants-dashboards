# P0 Consultant Workspace Reliability Checkpoint

## Repository state at checkpoint

- Branch: `codex/p0-role-workspace-routing`
- Starting HEAD: `22d18b0dcec8a7d4e4733a2b2ff797865a1a1396`
- Baseline before the final workspace-authority increment: `5f264ac021849915407fd1a3088e8f72d64a5d59`
- Pre-existing unrelated change: `services/practice-operations-service/app/fiteatsy_connections.py` (must remain untouched)
- Production security freeze: active; no deployment, credential rotation, session invalidation, or production-data mutation is authorised.

## Confirmed root causes

1. `api-gateway/app/routers/practice_tenant_resolver.py` resolves the authenticated consultant's canonical membership through the Fiteatsy backend (`/v1/auth/me`) instead of the Zestiva Auth service (`/api/v1/auth/me`).
2. `nuetra-frontend/lib/fiteatsyConsultantsApi.js` calls `GET /v1/external/clients`, but the authoritative Practice Operations client-directory contract is not exposed at that route.
3. Existing dashboard URLs do not provide the required canonical role-specific workspace namespace or one centralized backend-authority-based workspace guard.

## Required contracts

- Auth authority: `GET {AUTH_SERVICE_URL}/api/v1/auth/me` with the caller's bearer token returns `currentTenant` selected from active backend membership data.
- Gateway propagation: Practice Operations requests receive only server-derived `X-Tenant-Id`, `X-Tenant-Type`, and `X-User-Role`; caller-supplied authority headers are not trusted.
- Client directory: an authenticated, tenant-scoped Practice Operations endpoint returns only clients visible through assignment/consent rules and never fabricates an empty result on upstream failure.
- Workspace routing: canonical internal-consultant, external-consultant, senior-consultant, and super-admin URLs are guarded using `/auth/me` roles, permissions, and active membership context.

## Implemented increments

1. Auth → Gateway tenant resolution uses the canonical Auth `/api/v1/auth/me` contract.
2. Practice Operations exposes the authoritative tenant-scoped client directory and filters inactive consent connections.
3. Canonical role-specific workspace routes and a centralized guard protect internal consultant, external consultant, senior consultant, and super-admin workspaces.
4. `/auth/me` now exposes active `workspaceAuthorities`, including tenant, role, permissions, landing page, and resolution source.
5. Multiple active roles or tenants require explicit workspace selection. Missing/revoked authority is denied; a temporary authority-service failure is reported separately as recoverable.
6. The gateway validates any selected tenant against the authenticated user's active authorities before deriving upstream tenant headers.
7. Authorised legacy consultant deep links redirect to the canonical workspace while preserving query parameters.

## Verification and remaining release gates

- Auth service: 44 tests pass.
- API gateway: 51 tests pass (18 focused tenant-resolution tests).
- Practice Operations client-directory contract: 2 tests pass.
- Frontend workspace and isolation suites: 25 tests pass.
- Frontend production build: pass.
- Local browser regression: login redirect, direct deep-link authentication, manual role switching denial, legacy redirect/query preservation, refresh, back/forward, and explicit client-directory failure state pass with sample authenticated fixtures.
- Remaining blocker: integration/browser validation with real authenticated QA fixtures requires an approved QA environment and credentials. The production security freeze prohibits using production as a substitute.
- No deployment is authorised or performed by this work.
