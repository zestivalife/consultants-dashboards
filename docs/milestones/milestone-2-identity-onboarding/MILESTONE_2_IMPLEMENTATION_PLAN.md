# MILESTONE_2_IMPLEMENTATION_PLAN.md

# Milestone 2 — Identity & Onboarding Platform

Version: 1.0 (Draft)
Status: Architecture Approved – Implementation Planning
Owner: Platform Architecture
Implementation Owner: Engineering (Codex)
Review Owner: Product Owner

---

# 1. Executive Summary

## Objective

Implement a reusable Identity & Onboarding Platform capable of onboarding all current and future platform roles using a common workflow engine.

The platform shall support:

- Consultant
- Practitioner
- Mentor
- Organization Admin
- Corporate Admin
- Future configurable roles

without requiring role-specific onboarding code.

The implementation shall follow the Vertical Slice strategy defined in AGENTS.md and PROJECT_STATE.md.

No slice shall introduce regressions into the existing authentication or identity platform.

---

## Business Objectives

The implementation shall achieve the following measurable outcomes:

1. Eliminate manual user onboarding.
2. Support invitation-based onboarding.
3. Support configurable onboarding templates.
4. Support document verification.
5. Support approval workflow.
6. Support multi-role identities.
7. Support multiple Zestiva products.
8. Preserve existing authentication architecture.
9. Maintain backward compatibility with existing Platform Owner users.
10. Enable future onboarding flows without redesigning the platform.

---

## Technical Objectives

The implementation shall:

- Reuse the Identity Platform.
- Reuse RBAC.
- Reuse Audit Service.
- Reuse Notification Service.
- Reuse Email Service.
- Reuse Session Management.
- Reuse API Gateway.

No duplicate identity implementation is permitted.

---

# 2. Scope

## In Scope

The following capabilities are included in Milestone 2.

### Identity

- Invitation Engine
- Identity Activation
- Multi-role Assignment
- Account Activation
- User Status Lifecycle

---

### Onboarding

- Generic Onboarding Engine
- Template-driven onboarding
- Draft save
- Resume onboarding
- Submit onboarding
- Approval workflow
- Change request workflow

---

### Documents

- Document upload
- Document verification
- Document approval
- Document rejection

---

### Notifications

- Invitation email
- Reminder email
- Approval notification
- Rejection notification
- Activation notification

(Notification transport implementation is outside this milestone.)

---

### Administration

Super Admin

Organization Admin

Corporate Admin

Review Queue

Approval Queue

Pending Changes Queue

---

## Out of Scope

The following items SHALL NOT be implemented during Milestone 2.

- Scheduling
- Billing
- Payments
- Clinical consultation workflows
- AI recommendations
- Chat
- Video consultation
- Analytics dashboards
- Product-specific onboarding customizations
- Mobile application
- External identity providers (OAuth, SAML)
- MFA implementation (future milestone)

Decision:
Enterprise SSO is out of scope for Milestone 2 and will be addressed in a future milestone.

---

# 3. Engineering Principles

The following principles are mandatory.

## Principle 1

Business logic SHALL NOT exist inside React components.

PASS:
Business logic exists only inside backend services.

FAIL:
Business rules implemented inside UI.

---

## Principle 2

Identity SHALL remain generic.

PASS:
No Consultant-specific identity tables.

FAIL:
consultants table storing authentication information.

---

## Principle 3

Onboarding SHALL be template-driven.

PASS:
Adding a role requires configuration.

FAIL:
Adding a role requires backend code changes.

---

## Principle 4

One Vertical Slice per implementation.

PASS:
Each slice independently deployable.

FAIL:
Partial backend waiting for future frontend.

---

## Principle 5

No Mock Production Behaviour.

PASS:
Every screen connected to production APIs.

FAIL:
Temporary mock data.

---

## Principle 6

Every mutation generates an Audit Event.

PASS:
Audit event exists.

FAIL:
Database mutation without audit.

---

## Principle 7

Every API enforces RBAC.

PASS:
Permission validated.

FAIL:
Frontend-only permission checks.

---

# 4. Dependency Graph

Implementation Order

Foundation (Existing)
│
├── Identity Platform
├── Authentication
├── RBAC
├── Audit
├── API Gateway
└── Session Management
        │
        ▼
Slice 1
Invitation Engine
        │
        ▼
Slice 2
Password Setup
        │
        ▼
Slice 3
Email Verification
        │
        ▼
Slice 4
Generic Onboarding Engine
        │
        ▼
Slice 5
Document Management
        │
        ▼
Slice 6
Approval Workflow
        │
        ▼
Slice 7
Identity Activation
        │
        ▼
Slice 8
Role Assignment
        │
        ▼
Slice 9
Production Hardening
        │
        ▼
Milestone Acceptance

No slice may begin until all dependencies above it satisfy their acceptance criteria.

---

# 5. High-Level Work Breakdown

## Slice 1

Invitation Engine

Deliverables

- Invitation model
- Invitation API
- Invitation UI
- Invitation email trigger
- Audit events
- RBAC
- Tests

---

## Slice 2

Password Setup

Deliverables

- Password creation
- Password validation
- Password policy
- Secure activation
- Tests

---

## Slice 3

Email Verification

Deliverables

- Verification flow
- Expiration
- Resend
- Audit
- Tests

---

## Slice 4

Generic Onboarding Engine

Deliverables

- Wizard engine
- Template loader
- Draft saving
- Resume
- Submission
- Tests

---

## Slice 5

Document Management

Deliverables

- Upload
- Replace
- Delete
- Review
- Approval status
- Tests

---

## Slice 6

Approval Workflow

Deliverables

- Review queue
- Approve
- Reject
- Request changes
- Audit
- Notifications
- Tests

---

## Slice 7

Identity Activation

Deliverables

- Activate account
- Assign initial roles
- Enable login
- Audit
- Tests

---

## Slice 8

Role Assignment

Deliverables

- Multi-role assignment
- Role switching
- Permission recalculation
- Tests

---

## Slice 9

Production Hardening

Deliverables

- Runtime verification
- Regression testing
- Performance validation
- Security validation
- Production acceptance

---

# 6. Security & Secrets Handling

This document references authentication, invitation, and onboarding workflows.

The following must NEVER appear in documentation, code examples, or repository files:

- JWT signing keys
- Encryption keys
- Password hashes from production
- SMTP/API credentials
- Database credentials
- Cloud storage credentials
- Real access or refresh tokens

Secrets must be referenced only by placeholders such as:

- <ENV:DB_PASSWORD>
- <ENV:SMTP_API_KEY>
- <SECRETS_MANAGER:JWT_PRIVATE_KEY>
- {{ACCESS_TOKEN_PLACEHOLDER}}

No production hostnames, IP addresses, bucket names, or infrastructure identifiers are documented unless explicitly approved.

---

# Cross References

This document references the following implementation documents:

- MILESTONE_2_DATABASE_DESIGN.md (database schema and entity model)
- MILESTONE_2_API_SPECIFICATION.md (endpoint definitions)
- MILESTONE_2_UX_SPECIFICATION.md (screen and interaction behavior)
- MILESTONE_2_ARCHITECTURE_REVIEW.md (architectural validation)
- MILESTONE_2_ACCEPTANCE_REVIEW.md (pass/fail acceptance gates)
- README.md (source-of-truth order and canonical decisions)
- RBAC_SPECIFICATION.md (permissions and role responsibilities)
- NOTIFICATION_SPECIFICATION.md (outbox and notification events)
- AUDIT_LOG_SPECIFICATION.md (audit event requirements)
- EDGE_CASES.md (runtime edge cases)
- TEST_SCENARIOS.md (QA scenarios)
- ACCEPTANCE_CRITERIA.md (slice acceptance gates)
