

# Milestone 2 – Audit Log Specification

Version: 1.0

Status: Architecture Approved

Owner: Platform Architecture

## Purpose

This document defines mandatory audit behavior for Identity & Onboarding.

Audit logs are compliance records. They must be written transactionally with the business mutation whenever possible.

## Audit Event Shape

Every audit event must capture:

- `id`
- `event_type`
- `actor_user_id`
- `actor_role`
- `target_type`
- `target_id`
- `organization_id`
- `product_id`
- `old_value`
- `new_value`
- `metadata`
- `ip_address`
- `user_agent`
- `request_id`
- `created_at`

Sensitive values must be redacted before persistence.

## Required Events By Slice

| Slice | Events |
|---|---|
| Invitation Engine | `INVITATION_CREATED`, `INVITATION_RESENT`, `INVITATION_EXPIRED`, `INVITATION_CANCELLED` |
| Password Setup | `PASSWORD_CREATED`, `PASSWORD_POLICY_FAILED`, `PASSWORD_RESET_REQUESTED` |
| Email Verification | `EMAIL_VERIFICATION_SENT`, `EMAIL_VERIFIED`, `EMAIL_VERIFICATION_FAILED` |
| Onboarding Engine | `ONBOARDING_STARTED`, `ONBOARDING_DRAFT_SAVED`, `ONBOARDING_SUBMITTED`, `ONBOARDING_RESUMED` |
| Documents | `DOCUMENT_UPLOADED`, `DOCUMENT_REPLACED`, `DOCUMENT_DELETED`, `DOCUMENT_REVIEWED` |
| Approval | `ONBOARDING_APPROVED`, `ONBOARDING_REJECTED`, `CHANGES_REQUESTED`, `APPROVAL_REASSIGNED` |
| Activation | `ACCOUNT_ACTIVATED`, `LOGIN_ENABLED`, `ROLE_ASSIGNED` |
| Sessions | `LOGIN_SUCCEEDED`, `LOGIN_FAILED`, `SESSION_REFRESHED`, `LOGOUT`, `FORCE_LOGOUT` |

## Redaction Rules

Never store:

- Plaintext passwords
- Plaintext invitation tokens
- Refresh tokens
- Access tokens
- JWT secrets
- Database URLs
- Provider credentials

Store token fingerprints only when needed for support diagnostics.

## Query Requirements

Audit logs must support:

- Filtering by actor
- Filtering by target
- Filtering by event type
- Filtering by organization
- Filtering by product
- Date range
- Request ID lookup
- CSV export for authorized Super Admins

## Acceptance

No write operation in Milestone 2 is accepted unless a matching audit event can be verified in PostgreSQL.
