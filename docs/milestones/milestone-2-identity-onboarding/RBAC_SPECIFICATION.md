# Milestone 2 – RBAC Specification

Version: 1.0

Status: Architecture Approved

Owner: Platform Architecture

## Purpose

This document defines role and permission behavior for Identity & Onboarding.

Authentication must be identical for every user type. Authorization determines what each authenticated user can do.

## Role Vocabulary

| Display Role | System Role | Scope |
|---|---|---|
| Super Admin | `platform_owner` or existing superuser equivalent | Platform |
| Organization Admin | `organization_admin` | Organization |
| Corporate Admin | `corporate_admin` | Organization |
| Practitioner | `practitioner` | Organization, assigned clients |
| Mentor | `mentor` | Organization, assigned practitioners |
| Consultant | `consultant` | Organization, assigned clients |
| Future Role | configurable role | Defined by role template |

The UI may display "Super Admin"; the backend must continue using existing role keys unless an approved migration changes them.

## Permission Groups

Permissions are grouped by platform capability.

- Identity
- Invitations
- Onboarding
- Documents
- Approvals
- Organizations
- Users
- Roles
- Sessions
- Audit
- Notifications
- Settings

## Required Permissions

| Permission | Purpose |
|---|---|
| `users.read` | View users and profiles |
| `users.create` | Create users |
| `users.update` | Update users |
| `users.suspend` | Suspend or reactivate users |
| `users.invite` | Create and manage invitations |
| `roles.assign` | Assign roles |
| `roles.manage` | Create or update configurable roles |
| `onboarding.read` | View onboarding status |
| `onboarding.submit` | Submit own onboarding |
| `onboarding.review` | Review onboarding submissions |
| `documents.upload` | Upload own required documents |
| `documents.review` | Review submitted documents |
| `audit.read` | View audit logs |
| `sessions.manage` | Revoke sessions and force logout |

Slice 1 must use the existing `users.invite` permission.

## Role Responsibility Matrix

| Capability | Super Admin | Organization Admin | Corporate Admin | Practitioner | Mentor | Consultant |
|---|---|---|---|---|---|---|
| Create organizations | Yes | No | No | No | No | No |
| Create users | Yes | Scoped | Scoped employees | No | No | No |
| Send invitations | Yes | Scoped | Scoped employees | No | No | No |
| Reset accounts | Yes | Scoped | Scoped employees | No | No | No |
| Suspend users | Yes | Scoped | Scoped employees | No | No | No |
| Assign roles | Yes | Scoped | No | No | No | No |
| Manage licenses | Yes | Scoped view | Scoped view | No | No | No |
| View audit logs | Yes | Scoped | Scoped | Own | Scoped practitioners | Own |
| Conduct consultations | No | No | No | Yes | No | Assigned clients |
| Create treatment plans | No | No | No | Yes | Review only | Support only |
| Review practitioner work | No | No | No | No | Yes | No |
| Client onboarding | No | No | No | Assigned | Oversight | Yes |

## Enforcement Rules

- Backend permission checks are mandatory.
- Frontend visibility checks are not security controls.
- Every mutation must check both role and scope.
- Organization-scoped roles may access only assigned organization records.
- Product-scoped assignments must be checked when product scope exists.
- Future roles inherit permissions only from explicit role configuration.

## Regression Requirements

Every RBAC change must verify:

- Super Admin login and access.
- Organization Admin scoped access.
- Corporate Admin employee scope.
- Practitioner assigned client scope.
- Mentor assigned practitioner scope.
- Consultant assigned client scope.
- Unauthorized access returns 403 with no data leak.
