# Release Checklist

## Purpose

Mandatory release gate before any task is marked complete.

## Release Philosophy

Every change can introduce regressions. A task is complete only when the implementation, affected workflows, and unrelated critical modules are verified locally and, when deployed, in production.

## Release Workflow

1. Requirement Analysis
2. Architecture Review
3. Impact Analysis
4. Technical Design
5. Database Design
6. API Design
7. UX Review
8. Approval
9. Implementation
10. Local Verification
11. Regression Testing
12. Deployment
13. Production Verification
14. Acceptance
15. Update docs/delivery/PROJECT_STATE.md

No phase may be skipped.

## Risk Classification

- Low: Documentation, copy, non-functional styling, isolated UI polish.
- Medium: Single module logic, non-critical API, additive schema changes.
- High: Authentication, authorization, sessions, shared API client, migrations, gateway routing.
- Critical: Production outage, data loss risk, security issue, payment/auth failure.

## Pre-Implementation Checklist

- Requirement understood.
- Assumptions documented.
- Affected files identified.
- Affected services identified.
- Rollback path understood.

## Impact Analysis Checklist

- Frontend pages affected.
- Backend services affected.
- API endpoints affected.
- Database tables affected.
- Shared libraries affected.
- Authentication impact.
- Authorization impact.
- Session impact.
- Routing impact.
- Cache impact.
- Email impact.
- Notification impact.

## Regression Planning Checklist

- Existing flows to retest.
- Related modules to retest.
- Unrelated critical modules to smoke test.
- Data persistence checks.
- Browser refresh checks.
- Error-state checks.

## Local Verification Checklist

- Build passes.
- Tests pass.
- Lint/type checks pass where available.
- App starts locally where possible.
- No console runtime errors.

## Database Migration Checklist

- Migration created.
- Rollback migration created.
- Existing data preserved.
- Indexes and constraints reviewed.
- Migration tested against the correct database engine.

## API Verification Checklist

- Success response verified.
- Validation response verified.
- Authentication enforced.
- Authorization enforced.
- Error response shape verified.
- Request ID/logging verified.

## Frontend Verification Checklist

- Page loads.
- CTA works.
- Loading state appears.
- Empty state appears where applicable.
- Error state appears where applicable.
- Success notification appears.
- UI refreshes after mutation.

## Cross Module Regression Checklist

- Command Center.
- Organizations.
- People & Access.
- Permissions.
- Package Builder.
- Service Catalog.
- Practitioners.
- Mentors.
- Consultants.
- Reports.
- Audit Logs.
- Platform Health.
- Settings.

## Browser Runtime Verification

- Network has no unexpected failed requests.
- Console has no JavaScript errors.
- Local storage/session storage are correct.
- Browser refresh preserves expected state.

## Database Runtime Verification

- Records persisted.
- Soft delete works where applicable.
- Audit events created.
- Foreign keys valid.
- Queries are scoped by tenant/product/organization.

## Deployment Checklist

- Git commit pushed.
- Vercel deployment version verified.
- Railway deployment version verified where applicable.
- Environment variables verified.
- Migration applied.

## Rollback Checklist

- Last known good commit identified.
- Database rollback evaluated.
- Feature flags considered.
- User impact documented.

## Performance Verification

- Page load acceptable.
- API latency acceptable.
- Bundle size reviewed for frontend changes.
- Database query count reviewed for backend changes.
- No obvious N+1 query introduced.

## Security Verification

- No secrets committed.
- Input validation checked.
- Permission checks enforced.
- Sensitive data not logged.
- Session/token behavior verified for auth changes.

## Production Acceptance Checklist

- Production URL tested.
- Affected workflows tested.
- Unrelated critical workflows smoke tested.
- Browser console clean.
- Network clean.
- Database persistence verified.
- docs/delivery/PROJECT_STATE.md updated after accepted milestone.

## Required Release Report Format

- Git Commit:
- Deployment Version:
- Migration Version:
- Files Changed:
- Impact Analysis:
- Regression Checklist:
- Production Verification:
- Known Limitations:
- Network Verification:
- Database Verification:
- Production Ready: YES / NO
- docs/delivery/PROJECT_STATE.md Updated: YES / NO

## Known Limitations Format

- Limitation:
- Impact:
- Workaround:
- Owner:
- Follow-up:

## Definition of Production Ready

Production ready means the change works end-to-end in the deployed environment, persists correctly, enforces permissions, creates audit events where required, and does not regress affected or critical unrelated modules.

## Definition of Done

Done means implemented, reviewed, verified, deployed when required, regression-tested, and documented with the release report.

## Emergency Hotfix Process

1. Reproduce the production issue.
2. Identify the exact failing request/code path.
3. Apply the smallest safe fix.
4. Verify locally.
5. Deploy.
6. Verify production.
7. Document root cause and follow-up hardening.
