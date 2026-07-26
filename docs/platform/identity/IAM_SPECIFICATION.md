Document ID: PLATFORM-IDENTITY-003
Title: Identity & Access Management (IAM) Specification
Owner: Zestiva Platform Engineering
Status: APPROVED
Lifecycle: ACTIVE
Scope: Enterprise Identity & Access Management
Applies To: All Zestiva Products, Services and Applications
Last Updated: 2026-07-22
Supersedes: None
Depends On:
- IDENTITY_PLATFORM.md
- AUTHENTICATION_SPECIFICATION.md
Related Documents:
- PEOPLE_ACCESS_SPECIFICATION.md
- ../audit/AUDIT_PLATFORM.md

---

# Identity & Access Management (IAM)

## Executive Summary

The Identity & Access Management (IAM) Platform provides centralized authorization and access governance for the Zestiva ecosystem.

It manages roles, permissions, personas, capability bundles and access policies, ensuring users receive only the permissions required to perform their responsibilities.

Authentication verifies **who the user is**.

IAM determines **what the user is permitted to do**.

---

# Purpose

The IAM Platform exists to:

- Centralize authorization.
- Enforce Role-Based Access Control (RBAC).
- Manage permissions consistently.
- Support multiple personas.
- Enable delegated administration.
- Enforce least-privilege access.
- Maintain enterprise auditability.

---

# Business Context

Multiple Zestiva products share users, but each requires different capabilities.

Examples:

- Corporate Admin
- Practitioner
- Consultant
- Mentor
- Employee
- Super Admin

Without centralized IAM:

- Permission models diverge.
- Security becomes inconsistent.
- Administration becomes complex.
- Audit becomes fragmented.

The IAM Platform provides one authorization model for the entire ecosystem.

---

# Scope

## In Scope

- Roles
- Permissions
- Personas
- Permission Templates
- Capability Bundles
- RBAC
- Access Policies
- Delegated Administration
- Access Evaluation
- Privilege Management

## Out of Scope

- Authentication
- Password Management
- Session Management
- Business Workflows
- Product-specific Business Logic

---

# IAM Principles

## Least Privilege

Users receive only the permissions required.

---

## Deny by Default

Access is denied unless explicitly granted.

---

## Separation of Duties

Conflicting responsibilities shall not be assigned to the same identity unless explicitly approved.

---

## Policy Driven

Access decisions are based on configurable policies rather than hard-coded logic.

---

## Centralized Governance

Products consume IAM policies instead of implementing their own authorization rules.

---

# Core Components

## Role Engine

Defines organizational responsibilities.

Examples:

- Super Admin
- Corporate Admin
- Practitioner
- Consultant
- Mentor
- Employee

---

## Persona Engine

A user may operate under one or more personas.

Examples:

- Practitioner
- Mentor
- Consultant
- Corporate Administrator

Persona influences navigation, dashboards, workflows and application visibility.

---

## Permission Engine

Permissions represent individual actions.

Examples:

- User.Create
- User.Update
- User.Delete
- Report.View
- Assessment.Publish
- Wellness.Assign

---

## Permission Templates

Reusable collections of permissions.

Examples:

- Practitioner Standard
- Consultant Standard
- Corporate Admin
- Employee Self-Service

---

## Capability Bundles

Business capabilities assigned to users.

Examples:

- Nutrition
- Assessments
- Recovery Intelligence
- Reports
- Corporate Dashboard
- Wellness Programs

Capability bundles simplify product provisioning.

---

## Policy Engine

Evaluates authorization requests.

Inputs include:

- Identity
- Persona
- Role
- Permission Template
- Capability Bundle
- Requested Action

Outputs:

- Allow
- Deny

---

# Authorization Flow

```
Authenticated User

↓

Identity

↓

Persona

↓

Role

↓

Permission Template

↓

Capability Bundle

↓

Permission Evaluation

↓

Access Decision
```

---

# Access Model

```
Identity

↓

Persona

↓

Role

↓

Permission Template

↓

Capability Bundle

↓

Permissions

↓

Application Features
```

---

# RBAC Model

Each Role contains:

- Responsibilities
- Permissions
- Capability Bundles
- Navigation Access
- Administrative Privileges

RBAC shall remain configurable.

---

# Personas

A single identity may have multiple personas.

Examples:

- Consultant + Mentor
- Practitioner + Corporate Admin

Users may switch personas if permitted.

---

# Permission Categories

Examples:

## Read

View Data

---

## Create

Create Records

---

## Update

Modify Records

---

## Delete

Remove Records

---

## Approve

Approve Business Actions

---

## Administer

Administrative Functions

---

# Capability Bundles

Bundles group related business functionality.

Example:

Nutrition Bundle

- Meal Planning
- Diet Tracking
- Nutrition Reports

---

Assessment Bundle

- Assessments
- Questionnaires
- Recovery Analysis

---

Corporate Bundle

- Employee Management
- Wellness Dashboard
- Analytics

---

# Delegated Administration

Organizations may delegate administrative responsibilities.

Delegated administrators:

- Invite Users
- Assign Roles
- Reset Passwords
- Manage Teams

Delegation must never exceed granted permissions.

---

# Access Evaluation

Every protected request shall evaluate:

- Identity Status
- Authentication State
- Persona
- Role
- Capability Bundle
- Requested Resource
- Requested Action
- Policy Rules

---

# Administrative Policies

The IAM Platform shall support:

- Role Assignment
- Role Revocation
- Permission Assignment
- Permission Revocation
- Capability Assignment
- Persona Assignment

All changes require audit logging.

---

# Audit Events

Generate events for:

- Role Assigned
- Role Revoked
- Permission Granted
- Permission Revoked
- Persona Changed
- Capability Assigned
- Capability Removed
- Policy Updated

---

# API Endpoints

## Roles

GET /api/v1/roles

POST /api/v1/roles

PUT /api/v1/roles/{id}

DELETE /api/v1/roles/{id}

---

## Permissions

GET /api/v1/permissions

POST /api/v1/permissions

---

## Personas

GET /api/v1/personas

POST /api/v1/personas

---

## Capability Bundles

GET /api/v1/capabilities

POST /api/v1/capabilities

---

## Authorization

POST /api/v1/access/evaluate

---

# Security Requirements

The IAM Platform shall enforce:

- Least Privilege
- Deny by Default
- Role Validation
- Policy Validation
- Audit Logging
- Immutable Authorization Decisions
- Administrative Approval (where required)

---

# Non-Functional Requirements

Availability

99.9%

Performance

Authorization <100ms

Scalability

Millions of authorization requests

Reliability

High Availability

Observability

Full logging, metrics and tracing

---

# Dependencies

- Identity Platform
- Authentication Service
- Audit Platform
- Configuration Platform
- Observability Platform

---

# Acceptance Criteria

✓ Roles implemented.

✓ Personas implemented.

✓ Permissions implemented.

✓ RBAC operational.

✓ Capability Bundles operational.

✓ Policy Engine operational.

✓ Delegated Administration supported.

✓ Audit integration complete.

✓ APIs documented.

✓ Performance targets achieved.

---

# Future Enhancements

- Attribute-Based Access Control (ABAC)
- Policy-Based Access Control (PBAC)
- Context-Aware Authorization
- Risk-Based Authorization
- Fine-Grained Authorization
- Time-Based Permissions
- Geo-Based Access Policies
- AI-Assisted Policy Recommendations

---

# Revision History

| Version | Date | Author | Summary |
|----------|------------|------------------------------|--------------------------------|
| 1.0 | 2026-07-22 | Zestiva Platform Engineering | Initial IAM Specification |
