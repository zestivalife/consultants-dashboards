# MILESTONE_2_ENGINEERING_TASK_BREAKDOWN.md

# Milestone 2 – Identity & Onboarding Platform
## Engineering Task Breakdown

Version: 1.0

Status: Ready for Implementation

Owner: Platform Architecture

Related Documents

- MILESTONE_2_IMPLEMENTATION_PLAN.md
- MILESTONE_2_DATABASE_DESIGN.md
- MILESTONE_2_API_SPECIFICATION.md
- MILESTONE_2_UX_SPECIFICATION.md
- MILESTONE_2_ARCHITECTURE_REVIEW.md
- MILESTONE_2_ACCEPTANCE_REVIEW.md

---

# Purpose

This document breaks Milestone 2 into independent implementation tasks.

Each task must:

- be independently testable
- be independently deployable
- have clear acceptance criteria
- include rollback considerations
- avoid modifying unrelated modules

No task may span multiple vertical slices.

---

# Engineering Rules

Every task shall include:

- Objective
- Dependencies
- Expected Files
- Database Impact
- API Impact
- Frontend Impact
- RBAC Impact
- Audit Impact
- Regression Scope
- Acceptance Criteria
- Rollback Strategy

---

# Slice 1 — Invitation Engine

## Task 1.1

Create Invitation Domain Model

Objective

Create invitation entity and repository.

Dependencies

None

Database

user_invitations with additive migration fields only

Files

Repository

Service

Model

Tests

Complexity

Medium

Risk

Medium

Acceptance

Repository CRUD passes.

Rollback

Remove migration.

---

## Task 1.2

Invitation Service

Objective

Business rules.

Checks

Duplicate email

Duplicate invitation

Expiry

Status

Acceptance

All validations pass.

---

## Task 1.3

Invitation API

Endpoints

POST invitation

GET invitation

LIST invitation

Acceptance

OpenAPI contract matches API specification.

---

## Task 1.4

Invitation UI

Dialog

Validation

Loading

Errors

Acceptance

No mock data.

---

## Task 1.5

Audit

Generate events

INVITATION_CREATED

INVITATION_RESENT

INVITATION_EXPIRED and INVITATION_CANCELLED

Acceptance

Events recorded.

---

## Task 1.6

Regression

Verify

Authentication

People & Access

Permissions

Owner Dashboard

Acceptance

No regression.

---

# Slice 2 — Invitation Acceptance

## Task 2.1

Invitation Validation

Validation

Token hash lookup

Token expiry

Token revocation

Organization validation

Role validation

---

## Task 2.2

Invitation Status Transitions

Accepted

Expired

Revoked

Invalid

Audit events

Notification events

---

## Task 2.3

Invitation Acceptance UI

Landing Page

Expired Page

Revoked Page

Invalid Page

Accepted Page

Redirect to Password Setup

---

## Task 2.4

Regression

Invitation Engine

People & Access

Gateway routes

Token replay prevention

Audit/outbox persistence

---

# Slice 3 — Password Setup

## Task 3.1

Password Policy

---

## Task 3.2

Password Service

---

## Task 3.3

Password UI

---

## Task 3.4

Regression

Invitation

Activation

---

# Slice 4 — Authentication & Session

## Task 4.1

Login Regression

---

## Task 4.2

Session Restoration

---

## Task 4.3

Remember Me

---

## Task 4.4

Refresh Token Lifecycle

---

## Task 4.5

Logout

---

## Task 4.6

Logout All Devices

---

## Task 4.7

Regression

Authentication

Identity

Protected Routes

---

# Slice 5 — Profile Completion

## Task 5.1

Template Engine

---

## Task 5.2

Template Loader

---

## Task 5.3

Wizard Engine

---

## Task 5.4

Autosave

---

## Task 5.5

Resume

---

## Task 5.6

Submission

---

## Task 5.7

Regression

Authentication

Identity

Draft Recovery

---

# Slice 6 — Role-Specific Profiles

## Task 6.1

Practitioner Profile Template

---

## Task 6.2

Mentor Profile Template

---

## Task 6.3

Consultant Profile Template

---

## Task 6.4

Corporate Admin Profile Template

---

## Task 6.5

Future Role Configurability

---

## Task 6.6

Validation

---

## Task 6.7

Regression

Identity

Profile Completion

Permissions

---

# Slice 7 — Document Upload & Verification

## Task 7.1

Upload Service

---

## Task 7.2

Validation

---

## Task 7.3

Storage Integration

---

## Task 7.4

Preview

---

## Task 7.5

Review Queue

---

## Task 7.6

Regression

Upload

Delete

Download

---

# Slice 8 — Account Activation & Workspace Resolution

## Task 8.1

Approval Service

---

## Task 8.2

Approval Queue

---

## Task 8.3

Approve

---

## Task 8.4

Reject

---

## Task 8.5

Request Changes

---

## Task 8.6

Activation Service

---

## Task 8.7

Workspace Resolution

---

## Task 8.8

Dashboard Redirect

---

## Task 8.9

Regression

Sessions

Permissions

Dashboard

Navigation

---

# Global Acceptance Gates

Every task must satisfy:

Build

PASS

Tests

PASS

Runtime

PASS

RBAC

PASS

Audit

PASS

Regression

PASS

Security

PASS

Deployment

PASS

No task proceeds until the previous task is accepted.

---

# Security & Secrets Handling

No task shall:

- expose secrets
- expose JWTs
- expose passwords
- expose connection strings
- expose production infrastructure identifiers

Use placeholders only.

Examples:

<ENV:JWT_SECRET>

<ENV:SMTP_KEY>

<ENV:DB_PASSWORD>

{{ACCESS_TOKEN_PLACEHOLDER}}

---

# Cross References

Implementation Plan

See

MILESTONE_2_IMPLEMENTATION_PLAN.md

Database

See

MILESTONE_2_DATABASE_DESIGN.md

API

See

MILESTONE_2_API_SPECIFICATION.md

UX

See

MILESTONE_2_UX_SPECIFICATION.md

Acceptance

See

MILESTONE_2_ACCEPTANCE_REVIEW.md
