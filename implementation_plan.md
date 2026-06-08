# API Integration and Discrepancy Fixes

This plan outlines the steps required to align the Nuetra frontend (`nuetra-frontend`) with the Nuetra microservices backend, implement robust logging/error handling, and fix identified mapping mismatches.

## User Review Required

> [!WARNING]
> Please review the findings below regarding DB/backend changes. Since your request involves verifying the integration, this plan focuses heavily on ensuring the microservices interface accurately matches the frontend inputs and vice versa. 
> I propose to fix the API Gateway to prevent path stripping, as that is the root cause of `404 Not Found` for all microservices.

## Discrepancies Found

1. **API Gateway Path Stripping**:
   - **Mismatch**: The frontend currently requests (e.g., `/api/v1/auth/login`). The Gateway matches the `/api/v1/auth` prefix, strips it, and forwards only `/login` to `auth-service`. However, `auth-service` actually expects `/api/v1/auth/login`. This leads to complete 404 failures across the microservices architecture.
   - **Fix**: Modify `api-gateway/app/routers/proxy.py` to forward the `full_path` rather than the `remaining_path`.

2. **Assessment Payload Mismatch**:
   - **Mismatch**: Frontend (`lib/api.js`) sends `body: { responses }` for assessments. The backend schema (`SubmissionRequest`) strictly requires `body: { answers }`.
   - **Fix**: Update the frontend API wrappers to properly map `responses` to `answers`.

3. **Profile Payload Mismatch**:
   - **Mismatch**: The frontend's `pages/profile.js` allows users to edit `firstName`, `lastName`, and `phone` via `profileAPI.update()`. The backend route `/profile/me` (`FullProfileUpdate` schema) is designed exclusively for bio-metrics (age, sex, height, weight, biomarkers) and *does not* accept basic user demographic data. 
   - **Recommendation for Backend**: The `auth-service` database's User table needs new schema columns for `first_name`, `last_name`, `phone`, and `avatar`. The `/auth/me` and `/auth/register` DB contracts should be updated to return/accept these strings. 
   - **Frontend Fix**: During this frontend repair, I will adjust `profile.js` to ensure it doesn't crash from 422 errors due to sending unaccepted schema fields to the strict `/profile/me` bio-metric route.

## Proposed Changes

### nuetra-frontend

#### [MODIFY] [`lib/api.js`](file:///home/vector/projects/nuetra/nuetra-frontend/lib/api.js)
- Update `assessmentAPI` methods to wrap data in the explicit `{ answers: responses }` object.
- Implement debug console loggers dynamically logging Request Payload, Response Data, and Errors.
- Enhance error handling to parse 422 standard OpenAPI `loc` / `msg` formats to display precise text, capturing 500 standard outputs, and handling 401 correctly. 

#### [MODIFY] [`pages/profile.js`](file:///home/vector/projects/nuetra/nuetra-frontend/pages/profile.js)
- Explicitly map biological data (if present) or bypass submitting non-existent backend demographic fields (`firstName, lastName`) until backend schema is resolved. (I will attach a TO-DO tag for backend migration).

### api-gateway

#### [MODIFY] [`app/routers/proxy.py`](file:///home/vector/projects/nuetra/api-gateway/app/routers/proxy.py)
- Change line 61-62 to proxy the full route string `target_url = f"{upstream_base}{full_path}"` rather than cutting the matching prefix off.

## Verification Plan

### Automated/Manual Validation
- A helper script or curl sequence will be run directly against the API Gateway mapping the correct paths to verify all microservices respond with `200` or expected failures (e.g., `422/401`) instead of `404 Not Found`.
- I will programmatically drive the Complete Auth and Assessment flow via a mock Node.js script pointing to `NEXT_PUBLIC_API_URL` to validate end-to-end functionality.
