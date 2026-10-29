# External Consultant authentication recovery release manifest

## Scope

- Source branch: `codex/p0-external-consultant-auth-release`
- Baseline: `920d0d5151072e44a89463c74d69dab90b063a56`
- Release identity: the exact commit selected by the `Frontend Exact-SHA CI` workflow
- Production deployment: explicitly excluded from this change
- Fiteatsy production data and deployment: unchanged

## Confirmed defect

The consultant frontend and API gateway required `currentTenant`, but requested it
from Fiteatsy's `/v1/auth/me` response. The validated Fiteatsy contract does not
return consultant workspace membership, so valid External Consultant sessions
failed closed with `Workspace access unavailable`.

The consultant authentication service already stores the authoritative result of
External signup provisioning (`tenant_id` and `owner_membership_id`) and Internal
organization membership. This release projects only those persisted active records
into `/api/v1/auth/me`. Platform Owner sessions remain tenantless.

## Runtime contract

1. Authentication and refresh tokens continue to be issued and revoked only by
   the authentication service.
2. `/api/v1/auth/me` returns `currentTenant` only for:
   - completed External provisioning with both tenant and owner-membership IDs; or
   - an active Internal organization membership.
3. The frontend routes Platform Owners before consultant tenant hydration.
4. The API gateway resolves consultant tenant authority from the authentication
   service, then separately uses Fiteatsy for profession/client/consent data.
5. Tenant type, active status, membership resolution path, and authenticated user
   identity remain fail-closed at the gateway.

## Configuration preflight

Confirm presence without printing secret values:

- API gateway: `AUTH_SERVICE_URL`, `FITEATSY_SERVICE_URL`, `JWT_SECRET_KEY`.
- Authentication service: `DATABASE_URL`, `JWT_SECRET_KEY`,
  `FITEATSY_BACKEND_URL`, `FITEATSY_DELEGATION_PRIVATE_KEY`,
  `FITEATSY_DELEGATION_KEY_ID`.
- Frontend: `NEXT_PUBLIC_API_URL=https://api.nuetra.in` and the exact build SHA.
- The authentication service and gateway must share compatible token validation
  configuration.

## Database and rollback

- Schema migration: none.
- Data backfill: none.
- Production data mutation: none.
- Application rollback target: baseline commit
  `920d0d5151072e44a89463c74d69dab90b063a56`.
- Rollback action: redeploy the previous gateway, auth-service, and frontend
  artifacts together. No database rollback is required.

## Required release gates

- Exact-SHA parity in GitHub Actions.
- Full authentication-service, API-gateway, practice-operations, and frontend
  regression suites.
- Production frontend build.
- Dependency advisory review with documented disposition for every high or
  critical production dependency advisory.
- Authorised production smoke test for External Consultant login, correct tenant,
  foreign-tenant rejection, client linking, consent/revocation, reports, diet plans,
  and appointments.

## Deployment sequence (manual approval required)

1. Record the accepted exact SHA and successful CI URL.
2. Resolve or formally gate all open high/critical dependency advisories.
3. Verify the configuration names above in the production environment.
4. Deploy authentication service and wait for `/health` success.
5. Deploy API gateway and verify `/health` plus authenticated `/api/v1/auth/me`.
6. Deploy the frontend from the same exact SHA.
7. Confirm `/api/version` reports that SHA.
8. Perform authorised persona smoke tests; do not use a Platform Owner as an
   External Consultant substitute.
9. Roll back all three artifacts to the baseline if tenant resolution, isolation,
   or session refresh fails.
