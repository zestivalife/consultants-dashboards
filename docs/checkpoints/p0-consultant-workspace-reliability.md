# P0 Consultant Workspace Reliability Checkpoint

## Repository state at checkpoint

- Branch: `codex/p0-role-workspace-routing`
- Starting HEAD: `22d18b0dcec8a7d4e4733a2b2ff797865a1a1396`
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

## Remaining implementation stages

1. Correct Auth → Gateway tenant resolution and add focused regression coverage.
2. Add the Practice Operations client-directory endpoint and contract tests.
3. Add canonical role-specific workspace URLs and a centralized workspace guard with legacy redirects.
