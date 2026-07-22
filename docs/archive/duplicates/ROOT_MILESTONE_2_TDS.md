# Milestone 2 - Identity & Onboarding Workflow

---

Document Version : 1.0
Status           : APPROVED
Lifecycle        : FROZEN FOR IMPLEMENTATION

Project          : Zestiva Enterprise Platform
Milestone        : Milestone 2

Owner            : Product Owner
Engineering Lead : Codex

Approved By      : Lalit P. Paunikar
Approval Date    : 16 July 2026

Source of Truth  : Yes

Last Updated     : 16 July 2026

Related Documents

• PRD.md
• TDS.md
• ../../delivery/PROJECT_STATE.md
• MILESTONE_2_IMPLEMENTATION_PLAN.md
• MILESTONE_2_API_SPECIFICATION.md

---

# Technical Design Specification (TDS)

## Document Information

Product

Module

Milestone

Version

Status

Owner

Architecture Review Status

Last Updated

Related Documents

- PRD.md
- README.md
- MILESTONE_2_IMPLEMENTATION_PLAN.md
- MILESTONE_2_DATABASE_DESIGN.md
- MILESTONE_2_API_SPECIFICATION.md
- MILESTONE_2_UX_SPECIFICATION.md
- MILESTONE_2_ARCHITECTURE_REVIEW.md
- MILESTONE_2_ACCEPTANCE_REVIEW.md
- RBAC_SPECIFICATION.md
- NOTIFICATION_SPECIFICATION.md
- AUDIT_LOG_SPECIFICATION.md

---

# 1. Executive Summary

This document defines the technical approach for implementing the reusable Identity & Onboarding Platform across Nuetra, FitEatsy and future Zestiva products.

This document defines the system architecture, service boundaries, database interactions, APIs, workflows, integrations, deployment strategy, and engineering constraints.

---

# 2. Design Goals

The implementation SHALL:

- Be reusable.
- Be configurable.
- Be horizontally scalable.
- Be backward compatible.
- Be microservice friendly.
- Support multiple products.
- Support multiple organizations.
- Support multiple user roles.
- Avoid duplicated business logic.
- Preserve one shared application, login page, session system, identity service, routing system and design system.
- Resolve role-specific workspaces through identity, organization, permissions, licensed modules and feature flags.
- Generate navigation dynamically from resolved identity context instead of hardcoding sidebar items by role.

The implementation SHALL NOT:

- Create role-specific login pages.
- Create role-specific applications.
- Create role-specific session systems.
- Fork navigation architecture by user type.

---

# 3. High-Level Architecture

Presentation Layer

↓

Shared Application Shell

↓

Login

↓

Identity Resolution

↓

Organization Resolution

↓

Role and Permission Resolution

↓

Workspace Resolution

↓

Dashboard Loader

---

Service Architecture

↓

API Gateway

↓

Identity Service

↓

Workflow Service

↓

Notification Service

↓

Audit Service

↓

Storage Service

↓

PostgreSQL

↓

Redis

Every component shall have a single responsibility.

---

# 4. Service Responsibilities

Identity Service

- Authentication
- Users
- Roles
- Sessions
- Invitations

Workflow Service

- Onboarding
- Approvals
- State transitions

Notification Service

- Email
- Push
- SMS (future)

Audit Service

- Audit events
- Change history

Storage Service

- Documents
- Attachments

API Gateway

- Authentication
- Routing
- Rate limiting
- Correlation IDs

---

# 5. Identity Model

One human

↓

One identity

↓

Multiple role assignments

↓

Multiple organizations

↓

Multiple products

Identity SHALL NOT be duplicated.

---

# 6. Invitation Lifecycle

CREATED

↓

EMAIL_SENT

↓

OPENED

↓

PASSWORD_CREATED

↓

EMAIL_VERIFIED

↓

ONBOARDING_STARTED

↓

SUBMITTED

↓

APPROVED

↓

ACTIVATED

↓

LOGIN_ENABLED

Every transition must generate an audit event.

Slice 1 uses the existing Owner Console invitation route family and `user_invitations` storage model. No new invitation table may be introduced without approved architectural change.

---

# 7. Session Model

Access Token

↓

Refresh Token

↓

Session Record

↓

Device Registration

↓

Logout

↓

Revocation

Session restoration SHALL survive browser refresh according to Remember Me policy.

No session logic shall bypass the Identity Service.

---

# 8. Authentication Model

Authentication Flow

Login

↓

Credential Validation

↓

JWT Generation

↓

Refresh Token

↓

Session Persistence

↓

API Authorization

Authorization SHALL use RBAC.

Authentication SHALL remain independent of business modules.

---

# 9. Authorization Model

Permission

↓

Role

↓

Role Assignment

↓

Identity

↓

Organization

↓

Product

Permission evaluation SHALL occur on every protected request.

---

# 10. Generic Onboarding Engine

Template

↓

Sections

↓

Steps

↓

Fields

↓

Validation

↓

Submission

↓

Review

↓

Approval

↓

Activation

Adding a new role SHALL require template configuration only.

---

# 11. Document Management

Upload

↓

Virus Scan (future)

↓

Storage

↓

Metadata

↓

Review

↓

Approval

↓

Versioning

Document storage SHALL remain independent of onboarding.

---

# 12. Approval Workflow

Pending

↓

Assigned

↓

Review

↓

Approve

Reject

Request Changes

↓

Resubmit

↓

Approve

↓

Activate

Workflow SHALL be reusable by future modules.

---

# 13. Notification Flow

Business Event

↓

Notification Queue

↓

Email Service

↓

Delivery Log

↓

Audit

Notification delivery SHALL be asynchronous.

---

# 14. Audit Architecture

Business Action

↓

Audit Event

↓

Metadata

↓

Correlation ID

↓

Persistent Storage

Audit SHALL be immutable.

---

# 15. Error Handling Strategy

Validation Errors

Business Rule Errors

Authorization Errors

Infrastructure Errors

Unexpected Errors

Every error SHALL have:

- Error Code
- Message
- Correlation ID
- HTTP Status

No internal stack traces SHALL be returned.

---

# 16. Logging Strategy

Application Logs

Audit Logs

Security Logs

Infrastructure Logs

Sensitive values SHALL be masked.

---

# 17. Performance Targets

API Response

≤500 ms

Dashboard Load

≤2 seconds

Wizard Step

≤500 ms

Autosave

≤1 second

Document Upload

Progress displayed within 300 ms

---

# 18. Scalability Strategy

Stateless Services

Horizontal Scaling

Connection Pooling

Caching

Background Workers

Asynchronous Notifications

Template Versioning

Database Indexing

---

# 19. Reliability Strategy

Retry

Timeout

Circuit Breaker (future)

Graceful Failure

Idempotency

Rollback

Health Checks

---

# 20. Deployment Strategy

Backend

↓

Database Migration

↓

Gateway

↓

Frontend

↓

Health Checks

↓

Runtime Verification

↓

Acceptance

Zero-downtime deployment preferred.

---

# 21. Rollback Strategy

Application rollback.

Database rollback.

Migration rollback.

Feature flag disable.

Session validation.

Runtime verification.

Rollback SHALL restore the previous working state without data corruption.

---

# 22. Security Architecture

JWT Authentication

Refresh Token Rotation

RBAC

Audit Logging

Password Hashing

Encryption at Rest

HTTPS

Rate Limiting

Correlation IDs

Secret Management

Security SHALL follow SECURITY.md.

---

# 23. Engineering Constraints

No hardcoded roles.

No duplicate users.

No mock production workflows.

No frontend-only permissions.

No direct database access from UI.

No business logic inside React components.

No breaking changes to existing authentication.

---

# 24. Technical Decisions

Onboarding template rollback is supported by version pinning. Existing sessions continue on their pinned template version; new sessions use the active version.

Multiple reviewers may view a submission, but only one reviewer may hold the active review lock at a time.

Onboarding must be resumable across devices through server-side draft persistence.

---

# 25. Security & Secrets Handling

This document references authentication, sessions, notifications, and infrastructure.

The following SHALL NEVER appear:

JWT signing keys

Database passwords

SMTP credentials

Cloud credentials

Access tokens

Refresh tokens

Connection strings

Use placeholders only.

Examples

<ENV:JWT_PRIVATE_KEY>

<ENV:DB_PASSWORD>

<ENV:SMTP_API_KEY>

<ENV:REDIS_URL>

{{ACCESS_TOKEN_PLACEHOLDER}}

---

# 26. Cross References

Business Requirements

See PRD.md

Implementation Strategy

See MILESTONE_2_IMPLEMENTATION_PLAN.md

Database

See MILESTONE_2_DATABASE_DESIGN.md

API Contracts

See MILESTONE_2_API_SPECIFICATION.md

UX

See MILESTONE_2_UX_SPECIFICATION.md

Architecture Validation

See MILESTONE_2_ARCHITECTURE_REVIEW.md

Acceptance Criteria

See MILESTONE_2_ACCEPTANCE_REVIEW.md
