# MILESTONE_2_DATABASE_DESIGN.md

# Milestone 2 – Identity & Onboarding Platform
## Database Design Specification

Version: 1.0 (Draft)

Status: Architecture Approved – Database Design

Owner: Platform Architecture

Related Documents

- MILESTONE_2_IMPLEMENTATION_PLAN.md
- MILESTONE_2_API_SPECIFICATION.md
- MILESTONE_2_UX_SPECIFICATION.md
- MILESTONE_2_ARCHITECTURE_REVIEW.md
- MILESTONE_2_ACCEPTANCE_REVIEW.md

---

# 1. Purpose

This document defines the complete relational database design for the Identity & Onboarding Platform.

The design shall:

- support all current platform roles
- support future configurable roles
- remain product agnostic
- avoid schema redesign for new roles
- maintain auditability
- support enterprise scalability

This document intentionally contains **no implementation SQL**. It defines the canonical data model that implementation must follow.

---

# 2. Design Principles

The database shall satisfy the following principles:

1. Identity is independent of business role.

2. A user may hold multiple active roles.

3. Onboarding is template driven.

4. Invitations are independent from onboarding.

5. Documents are reusable.

6. Approval workflow is generic.

7. Every mutation is auditable.

8. No table shall be specific to Consultant, Mentor or Practitioner.

9. Business modules shall reference Identity rather than duplicate user information.

10. All primary keys shall use UUID.

---

# 3. Naming Standards

Primary Key

id

Foreign Key

<entity>_id

Boolean

is_active

is_deleted

Timestamps

created_at

updated_at

deleted_at

Audit

created_by

updated_by

deleted_by

Status

status

Version

version

---

# 4. Identity Domain

Core tables

users

user_roles

roles

permissions

role_permissions

login_sessions

refresh_tokens

user_devices

user_preferences

user_notifications

No business-specific data belongs in these tables.

---

# 5. Invitation Domain

Tables

user_invitations

invitation_events

invitation_email_outbox

invitation_token_history

Invitation lifecycle is independent of user lifecycle.

A user account may exist before an invitation.

An invitation may exist before onboarding begins.

Slice 1 SHALL reuse the existing `user_invitations` table with additive migration fields only.

Required invitation security fields:

- `token_hash`
- `token_fingerprint`
- `token_expires_at`
- `accepted_at`
- `expired_at`
- `cancelled_at`

The legacy `token` column, if present, must be redacted or unused. Plaintext invitation tokens must never be persisted.

---

# 6. Onboarding Domain

Tables

onboarding_templates

onboarding_template_versions

onboarding_steps

onboarding_fields

onboarding_rules

onboarding_sessions

onboarding_answers

onboarding_events

Templates must be configurable.

No role-specific onboarding tables are permitted.

---

# 7. Profile Domain

Tables

user_profiles

professional_profiles

organization_profiles

corporate_profiles

contact_information

address_information

Only profile-specific information belongs here.

Authentication data must never be duplicated.

---

# 8. Document Domain

Tables

documents

document_versions

document_categories

document_reviews

document_comments

document_audit

Documents shall support:

upload

replace

review

approve

reject

archive

---

# 9. Approval Domain

Tables

approvals

approval_steps

approval_comments

approval_history

approval_assignments

Workflow must support:

Approve

Reject

Request Changes

Escalate

Cancel

Reopen

---

# 10. Notification Domain

Tables

notification_queue

notification_templates

notification_preferences

notification_delivery_log

Notification transport is outside this milestone.

---

# 11. Audit Domain

Tables

audit_events

audit_metadata

audit_entity_changes

audit_login_events

Every mutation performed by the platform shall generate an audit event.

---

# 12. Relationship Model

User

↓

Role Assignment

↓

Invitation

↓

Onboarding Session

↓

Documents

↓

Approval

↓

Activation

↓

Dashboard Access

No relationship shall bypass Identity.

---

# 13. Multi Role Strategy

One user

↓

Many role assignments

↓

Many products

↓

Many onboarding sessions

↓

Many organizations

The schema must never require a duplicate user record.

---

# 14. State Machines

Invitation

DRAFT

CREATED

SENT

DELIVERED

OPENED

STARTED

EXPIRED

CANCELLED

COMPLETED

---

Onboarding

NOT_STARTED

IN_PROGRESS

DRAFT_SAVED

SUBMITTED

UNDER_REVIEW

CHANGES_REQUESTED

RESUBMITTED

APPROVED

REJECTED

ACTIVATED

---

Document

UPLOADED

UNDER_REVIEW

APPROVED

REJECTED

ARCHIVED

---

Approval

PENDING

UNDER_REVIEW

APPROVED

REJECTED

CHANGES_REQUESTED

ESCALATED

CANCELLED

---

# 15. Soft Delete Policy

Every business table shall support:

is_deleted

deleted_at

deleted_by

Authentication tables shall not use soft delete where security requires permanent revocation.

---

# 16. Versioning Strategy

The following entities shall support versioning:

Templates

Documents

Profile Definitions

Workflow Definitions

Version history shall remain immutable.

---

# 17. Index Strategy

Indexes shall exist for:

Primary Keys

Foreign Keys

Status

Email

Mobile Number

Invitation Token

Session Token Identifier

Approval Status

Organization

Role Assignment

Composite indexes shall be added only where justified by query patterns.

---

# 18. Sensitive Data Classification

The following columns SHALL be marked **[SENSITIVE]** during implementation.

users.email [SENSITIVE]

users.mobile [SENSITIVE]

users.password_hash [SENSITIVE]

refresh_tokens.token_hash [SENSITIVE]

login_sessions.ip_address [SENSITIVE]

login_sessions.device_identifier [SENSITIVE]

documents.storage_path [SENSITIVE]

professional_profiles.registration_number [SENSITIVE]

contact_information.address [SENSITIVE]

address_information.latitude [SENSITIVE]

address_information.longitude [SENSITIVE]

Handling Requirements

Passwords

Hash only.

Never reversible.

Tokens

Store hashed representation only.

PII

Encrypt at rest.

Mask in logs.

Never expose through audit events.

No plaintext credentials shall exist anywhere in the schema.

---

# 19. Data Retention Policy

Audit

Retain indefinitely.

Invitations

Configurable retention.

Expired invitations shall never be reused.

Sessions

Expired sessions may be archived.

Documents

Retention configurable by policy.

---

# 20. Security & Secrets Handling

This document references authentication, identity and sensitive user information.

The following must NEVER appear:

Database passwords

JWT secrets

Encryption keys

SMTP credentials

Cloud storage credentials

Session tokens

Refresh tokens

Connection strings

Use placeholders only.

Examples:

<ENV:DB_PASSWORD>

<ENV:POSTGRES_HOST>

<SECRETS_MANAGER:JWT_PRIVATE_KEY>

<ENV:STORAGE_BUCKET>

No production infrastructure identifiers shall be documented.

---

# 21. Architecture Decisions

Decision 1

Onboarding templates SHALL use a global base template with optional product and organization overrides. Slice 1 does not implement template overrides.

Decision 2

An onboarding session may resume after role reassignment only when the assigned template version remains the same. If the template changes, the previous session is archived and a new session is created.

Decision 3

Documents are reusable identity assets, but every onboarding session must reference the exact document version that satisfied a requirement.

---

# 22. Cross References

Implementation

See:

MILESTONE_2_IMPLEMENTATION_PLAN.md

API Contracts

See:

MILESTONE_2_API_SPECIFICATION.md

Screen Behaviour

See:

MILESTONE_2_UX_SPECIFICATION.md

Architecture Validation

See:

MILESTONE_2_ARCHITECTURE_REVIEW.md

Acceptance Criteria

See:

MILESTONE_2_ACCEPTANCE_REVIEW.md
