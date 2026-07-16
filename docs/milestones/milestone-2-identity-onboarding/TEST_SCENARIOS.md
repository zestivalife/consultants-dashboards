# Milestone 2 – Test Scenarios

Version: 1.0

Status: Architecture Approved

Owner: QA Architecture

## Test Strategy

Every slice must include:

- Unit tests
- Repository tests
- Service tests
- API integration tests
- RBAC tests
- Audit verification
- Database migration tests
- Browser runtime tests
- Regression tests for authentication and sessions

## Role Coverage

Test users must cover:

- Super Admin
- Organization Admin
- Corporate Admin
- Practitioner
- Mentor
- Consultant
- Future configurable role

## Slice 1 – Invitation Engine

| Test ID | Scenario | Expected Result |
|---|---|---|
| M2-S1-001 | Super Admin creates invitation | 201, `user_invitations` row persisted |
| M2-S1-002 | User without `users.invite` creates invitation | 403 |
| M2-S1-003 | Duplicate pending invitation | 409 |
| M2-S1-004 | Resend invitation | New token hash, previous token invalid |
| M2-S1-005 | Expire invitation | Status becomes `EXPIRED` |
| M2-S1-006 | Token plaintext storage check | No plaintext token exists |
| M2-S1-007 | Outbox check | `invitation_email_outbox` status `PENDING` |
| M2-S1-008 | Audit check | `INVITATION_CREATED`, `INVITATION_RESENT`, `INVITATION_EXPIRED` exist |

## Authentication Regression

| Test ID | Scenario | Expected Result |
|---|---|---|
| AUTH-001 | Login as each role | Login succeeds for valid credentials |
| AUTH-002 | Browser refresh | Session restored |
| AUTH-003 | Remember Me enabled and browser restart | Session restored |
| AUTH-004 | Remember Me disabled and browser restart | Session ends |
| AUTH-005 | Expired access token | Silent refresh succeeds |
| AUTH-006 | Expired refresh token | User redirected to login |
| AUTH-007 | Logout | Session revoked and storage cleared |

## Browser Acceptance

Every browser test must verify:

- No console errors.
- No unhandled promise rejections.
- No failed network requests except expected validation failures.
- Loading states clear.
- Success and error states are visible.
- Browser refresh preserves expected state.
