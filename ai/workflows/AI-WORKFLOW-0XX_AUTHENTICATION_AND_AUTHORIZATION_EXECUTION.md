# Authentication & Authorization Execution Workflow

**Document ID:** AI-WORKFLOW-0XX

**Version:** 1.0.0

**Status:** APPROVED

**Classification:** Enterprise Runtime Execution Workflow

**Owner:** Enterprise Platform Architecture Office

---

# Purpose

This workflow defines the complete execution lifecycle from user creation through successful login and authorised application access.

It serves as the canonical execution model for all authentication, identity, RBAC, product access, capability bundles and dashboard routing across the Enterprise AI Operating System (EAIOS).

Whenever a login, permission or access issue occurs, this document SHALL be used as the primary troubleshooting workflow.

---

# Workflow Overview

```text
Create User
      │
      ▼
Create Identity
      │
      ▼
Send Invitation
      │
      ▼
Accept Invitation
      │
      ▼
Activate Identity
      │
      ▼
Assign Role
      │
      ▼
Assign Permission Bundle
      │
      ▼
Assign Capability Bundle
      │
      ▼
Assign Product
      │
      ▼
Assign Organization
      │
      ▼
Synchronize Assignments
      │
      ▼
Generate Access Profile
      │
      ▼
User Login
      │
      ▼
Authentication
      │
      ▼
Issue JWT
      │
      ▼
Load User Context
      │
      ▼
Resolve Permissions
      │
      ▼
Resolve Landing Dashboard
      │
      ▼
Validate Route
      │
      ▼
Generate Navigation
      │
      ▼
Application Access
```

---

# Execution Stages

## Stage 1 — Identity Creation

Input

- Name
- Email
- Mobile
- Product
- Organization

Validation

✓ Email unique

✓ Mobile unique

✓ Identity created

Output

Identity ID

---

## Stage 2 — Invitation

Actions

- Generate Invite Token
- Send Email
- Send WhatsApp
- Expiry

Validation

✓ Token valid

✓ Invitation active

Output

Pending User

---

## Stage 3 — Activation

Actions

- Set Password
- Accept Terms
- Verify Email
- Verify Mobile

Validation

✓ Password created

✓ Identity activated

Output

ACTIVE User

---

## Stage 4 — Role Assignment

Input

Role

Example

- Super Admin
- Corporate Admin
- Consultant
- Mentor
- Practitioner
- Employee

Validation

✓ Role exists

✓ Role active

Output

Primary Role

---

## Stage 5 — Permission Bundle

Assign

Permission Set

Example

```text
Practitioner

↓

View Dashboard

Update Profile

Access Sessions

Access Clients

NO Owner Permissions
```

Validation

✓ Bundle assigned

Output

Permission Bundle ID

---

## Stage 6 — Capability Bundle

Assign

Capabilities

Example

```text
Nutrition

Assessments

Reports

Calendar

Consultations
```

Validation

✓ Capability bundle attached

---

## Stage 7 — Product Assignment

Assign

Products

Example

```text
FitEatsy

Nuetra

Recovery

Corporate Wellness
```

Validation

✓ Product active

✓ Product licensed

---

## Stage 8 — Organization Assignment

Assign

- Organization
- Department
- Branch

Validation

✓ Organization exists

✓ User belongs to organization

---

## Stage 9 — Assignment Synchronization

Actions

Synchronize

- Roles
- Permissions
- Capabilities
- Products
- Organizations

Generated

```text
Effective Access Profile
```

Validation

✓ No stale cache

✓ Access profile rebuilt

---

## Stage 10 — Authentication

User Login

↓

Validate Password

↓

Validate Identity

↓

Validate Status

↓

Generate Session

↓

Generate JWT

Validation

✓ ACTIVE

✓ Email verified

✓ Not suspended

Output

JWT Token

---

## Stage 11 — Context Resolution

Load

- User
- Organization
- Product
- Role
- Permissions
- Capabilities

Generate

```text
Execution Context
```

---

## Stage 12 — Authorization

Resolve

```text
Role

+

Permission Bundle

+

Capability Bundle

+

Organization

+

Product

↓

Effective Permissions
```

Output

```text
Permission Matrix
```

---

## Stage 13 — Landing Dashboard Resolution

Rules

Super Admin

↓

Owner Dashboard

Corporate Admin

↓

Corporate Dashboard

Consultant

↓

Consultant Dashboard

Mentor

↓

Mentor Dashboard

Practitioner

↓

Practitioner Dashboard

Employee

↓

Employee Dashboard

Validation

✓ Dashboard exists

✓ Permission valid

---

## Stage 14 — Route Authorization

Example

```text
/dashboard/owner/*
```

Allowed

Super Admin

Corporate Admin

Denied

Practitioner

Mentor

Employee

Validation

403 if unauthorized

---

## Stage 15 — Navigation Generation

Generate

Sidebar

Menu

Quick Actions

Widgets

Hidden Pages

Based on

Permission Matrix

---

## Stage 16 — Runtime Access

User enters application

↓

Menus generated

↓

APIs enabled

↓

Dashboard loaded

↓

Session started

SUCCESS

---

# Validation Checklist

Identity

□ Exists

□ Active

□ Verified

Role

□ Assigned

□ Active

Permissions

□ Bundle Assigned

Capabilities

□ Bundle Assigned

Organization

□ Assigned

Product

□ Assigned

Authentication

□ JWT Generated

□ Session Created

Authorization

□ Permission Matrix Generated

□ Dashboard Assigned

□ Route Validated

Navigation

□ Menu Generated

□ Widgets Generated

---

# Root Cause Decision Tree

## Login Failed

Check

- Identity
- Password
- Status
- Email Verification

---

## Login Success + Access Denied

Check

- Role

- Permission Bundle

- Capability Bundle

- Product Assignment

- Organization Assignment

- Route Mapping

- Dashboard Resolution

---

## Empty Sidebar

Check

- Menu Generator

- Permission Matrix

- Cached Permissions

---

## Wrong Dashboard

Check

- Landing Route Resolver

- Role Mapping

- Product Context

---

## API Returns 403

Check

Backend RBAC

↓

JWT Claims

↓

Permission Resolver

↓

API Policy

---

# Database Validation

Verify

Users

Roles

Role Assignments

Permission Bundles

Capability Bundles

Organization Membership

Products

Sessions

JWT Claims

Audit Logs

---

# APIs Participating

Identity Service

Invitation Service

Authentication Service

Authorization Service

People Service

Organization Service

RBAC Service

Navigation Service

Dashboard Service

Audit Service

---

# AI Troubleshooting Prompt

When an access issue occurs, the AI SHALL answer:

1. Which execution stage failed?

2. Which API produced incorrect data?

3. Which database entity is inconsistent?

4. Which permission is missing?

5. Which capability is missing?

6. Which dashboard should have been assigned?

7. Which route should have been allowed?

8. Which service owns the defect?

9. Is the issue frontend, backend or configuration?

10. Provide the exact corrective actions.

---

# Success Criteria

The workflow is considered successful when:

✓ Identity is ACTIVE

✓ Invitation accepted

✓ Role assigned

✓ Permission bundle attached

✓ Capability bundle attached

✓ Product assigned

✓ Organization assigned

✓ JWT generated

✓ Effective Permission Matrix generated

✓ Correct Dashboard loaded

✓ Correct Menu generated

✓ Authorized APIs accessible

✓ User reaches intended landing page without manual intervention
