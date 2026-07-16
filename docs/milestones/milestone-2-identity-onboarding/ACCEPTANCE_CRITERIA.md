

# Milestone 2 – Acceptance Criteria

Version: 1.0

Status: Architecture Approved

Owner: Product Owner and Chief Architect

## Purpose

This document provides implementation-ready acceptance criteria. The production acceptance review remains in `MILESTONE_2_ACCEPTANCE_REVIEW.md`.

## Milestone Acceptance

Milestone 2 is accepted only when all slices pass:

- Invitation Engine
- Invitation Acceptance
- Password Setup
- Authentication & Session
- Profile Completion
- Role-Specific Profiles
- Document Upload & Verification
- Account Activation & Workspace Resolution

## Slice Acceptance Template

Every slice must provide:

- Impact Analysis
- Risk Score
- Architecture Review
- Regression Plan
- Migration Plan
- Rollback Plan
- Local Build Evidence
- Test Evidence
- Production Deployment Evidence
- Browser Runtime Evidence
- Database Evidence
- Audit Evidence
- Known Limitations
- Final Status

## Slice 1 Acceptance

Invitation Engine is accepted only when:

- `POST /api/v1/owner/people-access/invitations` creates a live invitation.
- Duplicate invitation prevention works.
- Resend generates a new token hash and outbox event.
- Expire marks invitation expired.
- `user_invitations.token` is redacted or unused.
- `user_invitations.token_hash` is populated.
- `user_invitations.token_fingerprint` is populated.
- `invitation_email_outbox` contains a `PENDING` record.
- `INVITATION_CREATED`, `INVITATION_RESENT` and `INVITATION_EXPIRED` audit events exist.
- Login, Remember Me, browser refresh and browser restart still work.
- No browser console errors or unexpected failed network requests occur.

## Slice 2 Acceptance

Invitation Acceptance is accepted only when:

- Invitation landing page validates a secure token without exposing plaintext token data.
- Valid invitation token returns organization, role, expiry and next-step metadata.
- Expired invitation renders the expired state and records the required audit event.
- Revoked invitation renders the revoked state and records the required audit event.
- Invalid invitation renders the invalid state without leaking token or account data.
- Accepted invitation transitions status to `ACCEPTED`.
- Accepted invitation cannot be replayed.
- Organization validation and role validation pass before acceptance.
- Notification outbox records are created for Slice 2 invitation acceptance events.
- Redirect to Password Setup is returned without creating a password.
- Password creation, profile completion, document upload and workspace loading are not implemented in this slice.
- No authentication, session, RBAC, or gateway regressions occur.

## Non-negotiable Failure Conditions

The milestone remains `BLOCKED` if:

- A route exists only in the frontend.
- A button has no backend mutation.
- A mutation writes no audit event.
- Plaintext tokens are persisted.
- Password hashing is duplicated.
- Authentication differs by role.
- Browser refresh logs out a valid session.
- Migration head differs from production.
- Production runtime differs from expected commit.
