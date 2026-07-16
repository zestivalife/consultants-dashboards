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

# Slice 2 — Password Setup

## Task 2.1

Password Policy

Validation

Minimum length

Uppercase

Lowercase

Special

Number

---

## Task 2.2

Password Service

Hashing

Verification

Expiry

---

## Task 2.3

Password UI

Create

Confirm

Strength Meter

Errors

---

## Task 2.4

Regression

Login

Logout

Remember Me

Session

Refresh

---

# Slice 3 — Email Verification

## Task 3.1

Verification Token

---

## Task 3.2

Verification Service

---

## Task 3.3

Verification UI

---

## Task 3.4

Regression

Invitation

Password

Activation

---

# Slice 4 — Generic Onboarding

## Task 4.1

Template Engine

---

## Task 4.2

Template Loader

---

## Task 4.3

Wizard Engine

---

## Task 4.4

Autosave

---

## Task 4.5

Resume

---

## Task 4.6

Submission

---

## Task 4.7

Regression

Authentication

Identity

Draft Recovery

---

# Slice 5 — Document Management

## Task 5.1

Upload Service

---

## Task 5.2

Validation

---

## Task 5.3

Storage Integration

---

## Task 5.4

Preview

---

## Task 5.5

Review Queue

---

## Task 5.6

Regression

Upload

Delete

Download

---

# Slice 6 — Approval Workflow

## Task 6.1

Approval Service

---

## Task 6.2

Approval Queue

---

## Task 6.3

Approve

---

## Task 6.4

Reject

---

## Task 6.5

Request Changes

---

## Task 6.6

Notifications

---

## Task 6.7

Regression

Identity

Workflow

Audit

---

# Slice 7 — Identity Activation

## Task 7.1

Activation Service

---

## Task 7.2

Initial Role Assignment

---

## Task 7.3

Enable Login

---

## Task 7.4

Welcome Notification

---

## Task 7.5

Regression

Sessions

Permissions

Login

---

# Slice 8 — Multi Role Assignment

## Task 8.1

Assign Role

---

## Task 8.2

Remove Role

---

## Task 8.3

Switch Active Role

---

## Task 8.4

Permission Recalculation

---

## Task 8.5

Regression

RBAC

Dashboard

Navigation

---

# Slice 9 — Production Hardening

## Task 9.1

Performance Review

---

## Task 9.2

Security Review

---

## Task 9.3

Accessibility Review

---

## Task 9.4

Regression Testing

---

## Task 9.5

Production Deployment

---

## Task 9.6

Production Acceptance

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
