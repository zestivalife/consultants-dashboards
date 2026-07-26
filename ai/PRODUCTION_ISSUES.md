# Production Issues

## PROD-001 — People & Access Post-Authentication Access Resolution

**Status:** CLOSED  
**Closed Commit:** `b94a337d34a746a8105b7b804368531b06e7f041`  
**Production Verification Date:** 2026-07-26

### Root Cause

Authenticated users were routed after login using incomplete frontend role-to-dashboard mappings. Valid users with roles such as `practitioner` could authenticate successfully, receive JWT/session state, and pass backend authorization, but the frontend resolved an incorrect landing page and then blocked the user through route guards.

### Fix Summary

- Added an auth-service `access_profile` to login/session user responses.
- Resolved workspace context from People & Access organization/product/permission data.
- Replaced hardcoded frontend dashboard routing with generic access-profile and permission-based workspace resolution.
- Updated route guards and shared redirects to evaluate access policies instead of incomplete static role maps.
- Added auth-service regression coverage for practitioner workspace resolution.

### Production Verification

- Frontend production version endpoint reports commit `b94a337d34a746a8105b7b804368531b06e7f041`.
- API Gateway production version endpoint reports commit `b94a337d34a746a8105b7b804368531b06e7f041`.
- Auth-service production version endpoint reports commit `b94a337d34a746a8105b7b804368531b06e7f041`.
- Platform Owner login resolves to workspace `platform-operations` and landing page `/dashboard/owner`.
- Production-created practitioner login resolves to workspace `care-delivery` and landing page `/dashboard/provider`.
- Production temporary-password flow for practitioner succeeds and final login returns `must_change_password=false`.
- Production-created `corporate_admin`, `mentor`, and `consultant` users resolve to their expected workspaces.

### Validation

- Backend compile passed for `services/auth-service/app`.
- Auth-service regression tests passed: `29 passed`.
- Frontend production build passed.

### Known Limitations

- Automated browser-console verification was not executed because `agent-browser` is unavailable in the current Codex runtime. Runtime API, deployment, and route-resolution verification were completed against production.
