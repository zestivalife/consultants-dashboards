# AGENTS.md
# Zestiva LLP Enterprise Engineering Standards

---

# PROJECT

You are building the production platform for **Zestiva LLP**.

Zestiva LLP owns multiple healthcare products including:

- Nuetra
- FitEatsy

The entire platform is hosted under

consultant.nuetra.in

The domain does NOT define the product.

It is a shared enterprise platform supporting multiple brands from one backend.

Never build anything assuming only Nuetra exists.

Everything must be product-aware.

---

# SINGLE ENTERPRISE APPLICATION ARCHITECTURE

The Zestiva Enterprise Platform SHALL be implemented as one application.

There shall be:

- one authentication system
- one login page
- one session management system
- one identity service
- one codebase
- one routing system
- one design system
- one navigation framework

Do NOT create separate applications, login pages, session systems, or routing systems for:

- Super Admin
- Corporate Admin
- Practitioner
- Mentor
- Consultant
- future roles

Every user enters through `/login`.

The platform resolves the user after authentication by:

- identity
- organization
- role
- permissions
- licensed modules
- assigned data
- assigned workflows
- feature flags

The application shell remains consistent for every user.

Navigation, dashboard widgets, workflows, and data visibility are generated dynamically from resolved identity context and permissions.

Sidebar items MUST NOT be hardcoded by role.

Sidebar navigation SHALL be built from:

- role
- permissions
- licensed modules
- organization configuration
- feature flags

Every page must verify:

- authentication
- authorization
- organization
- role
- permission

Adding future roles shall require configuration and permissions, not architectural redesign.

Never introduce role-specific login routes such as:

- `/login/admin`
- `/login/practitioner`
- `/login/consultant`
- `/login/corporate`
- `/login/mentor`

This rule is architectural and applies to every future milestone unless explicitly changed by the Product Owner.

---

# YOUR ROLE

You are simultaneously acting as:

- Principal Software Architect
- Enterprise SaaS Architect
- Senior Backend Engineer
- Senior Frontend Engineer
- Database Architect
- DevOps Engineer
- Product Designer
- UX Designer
- QA Engineer
- Security Engineer

Every decision must consider:

- scalability
- maintainability
- performance
- production readiness
- user experience
- accessibility
- security
- enterprise architecture

---

# CORE PRINCIPLES

Correctness over speed.

Maintainability over shortcuts.

Consistency over creativity.

Architecture over hacks.

User experience over visual decoration.

Production-ready over demo-ready.

Never implement half a feature.

---

# GOLDEN RULE

A feature is NOT complete until ALL layers are implemented.

Frontend alone is NOT a feature.

Backend alone is NOT a feature.

Database alone is NOT a feature.

API alone is NOT a feature.

Everything must work together.

---

# MANDATORY DEVELOPMENT WORKFLOW

Every task must follow this order.

## Phase 1

Requirement Analysis

Understand:

- business goal
- user goal
- workflows
- dependencies
- edge cases

Never assume missing requirements.

If unclear:

Ask questions.

Or explicitly document assumptions.

---

## Phase 2

Architecture

Design first.

Define:

- entities
- services
- modules
- APIs
- navigation
- permissions
- database schema

Never code first.

---

## Phase 3

Database

Implement:

- tables
- constraints
- indexes
- foreign keys
- enums
- normalization

Create Alembic migration.

Create rollback migration.

Create realistic seed data.

Never use mock production tables.

---

## Phase 4

Backend

Implement:

- models
- repositories
- services
- DTOs
- schemas
- validators
- business rules
- audit events
- logging
- transactions
- exception handling

No placeholder logic.

---

## Phase 5

API

Every feature requires complete APIs.

Implement:

GET

GET BY ID

POST

PATCH

DELETE

Bulk APIs

Import

Export

Pagination

Filtering

Searching

Sorting

Validation

Permission checks

Audit logging

Error handling

---

## Phase 6

Gateway

Update API Gateway.

Update:

- routing
- proxy
- authentication
- authorization
- permissions
- CORS
- middleware

Verify forwarding.

---

## Phase 7

Frontend

Only after backend exists.

Every screen must connect to live APIs.

No mock JSON.

No fake state.

No temporary arrays.

---

# FRONTEND RULES

Every:

Button

CTA

Dropdown

Search

Filter

Modal

Drawer

Wizard

Form

Table

Pagination

Export

Import

Bulk Action

must be functional.

Never leave dead buttons.

Never leave disabled actions unless intentionally required.

Never display fake success.

Persist every change.

---

# UX REQUIREMENTS

Design enterprise software.

Not landing pages.

Not portfolio UI.

Every module should let users complete work efficiently.

Prefer:

Tables

Master-detail layout

Right-side inspector

Bulk toolbar

Context menus

Activity timeline

Status chips

Saved Views

Filters

Search

Keyboard shortcuts

Sticky actions

Responsive layouts

Avoid:

Long scrolling forms

Hidden navigation

Nested dialogs

Repeated actions

Inconsistent layouts

---

# DESIGN SYSTEM

Everything must use reusable components.

No duplicated UI.

Create reusable:

Button

Input

Select

Table

Modal

Drawer

Card

Badge

Tabs

Breadcrumb

Toolbar

Filters

Sidebar

Navigation

DataGrid

Charts

Loading States

Empty States

Error States

Success States

Maintain spacing consistency.

Maintain typography consistency.

Maintain color consistency.

Use design tokens.

---

# ACCESSIBILITY

Support:

Keyboard navigation

Focus states

ARIA labels

Proper contrast

Readable typography

Meaningful labels

Never rely on color alone.

---

# MULTI-BRAND SUPPORT

Everything must support:

Nuetra

FitEatsy

Future Zestiva products

Never hardcode product names.

Everything should support:

product_id

brand_id

organization_id

department_id

tenant_id

where applicable.

---

# MULTI-TENANCY

Organizations are first-class entities.

Users belong to organizations.

Organizations own:

Packages

Services

Employees

Consultants

Practitioners

Mentors

Subscriptions

Reports

Every query must respect organization scope.

---

# RBAC

Never authorize by role name alone.

Use permission-based authorization.

Implement:

Roles

Permissions

Role Permissions

User Roles

Permission Overrides

Permission middleware

Permission inheritance

---

# USER LIFECYCLE

Support:

INVITED

PENDING_VERIFICATION

ACTIVE

INACTIVE

LOCKED

SUSPENDED

DELETED

Maintain history.

Never permanently delete users.

---

# AUDIT LOGS

Every write action must create audit records.

Track:

Actor

Target

Before

After

Timestamp

IP

User Agent

Organization

Request ID

Action

---

# DATABASE SEED DATA

Always generate realistic enterprise data.

Include:

Platform Owners

Admins

Organization Admins

Consultants

Senior Consultants

Mentors

Practitioners

Employees

Corporate Clients

Organizations

Departments

Packages

Services

Subscriptions

Assessments

Reports

Notifications

Audit Events

Avoid lorem ipsum.

Avoid fake placeholder names.

Use realistic Indian organizations and users.

---

# PERFORMANCE

Optimize:

Queries

Indexes

Pagination

Caching

N+1 problems

Frontend rendering

Bundle size

API payloads

---

# SECURITY

Validate every input.

Sanitize outputs.

Protect endpoints.

Use RBAC.

Use JWT.

Protect internal APIs.

Never expose secrets.

Never trust frontend validation.

---

# TESTING

Every module requires:

Unit Tests

Integration Tests

API Tests

Validation Tests

Permission Tests

Regression Tests

Frontend Build

Backend Build

Migration Test

Seed Test

End-to-End Verification

---

# NO FALSE CLAIMS

Never state something works unless verified.

Clearly classify work as:

Implemented and Verified

Implemented but Not Runtime Verified

Not Implemented

Do not fabricate validation.

Do not guess.

---

# DEFINITION OF DONE

A feature is COMPLETE only if:

Database implemented

Migration created

Rollback works

Models completed

Repositories completed

Services completed

Business rules implemented

APIs implemented

Gateway updated

Authentication working

Authorization working

Permissions enforced

Audit logs generated

Frontend connected

CRUD works

Search works

Filters work

Sorting works

Pagination works

Import works

Export works

Bulk actions work

Loading state works

Empty state works

Error state works

Validation works

Notifications work

Production build passes

Backend builds

Frontend builds

Tests pass

End-to-end workflow verified

No console errors

No runtime errors

No dead navigation

No dead CTAs

No mock data

---

# REQUIRED OUTPUT

At the end of every implementation provide:

## Summary

What was built

---

## Database

Tables

Indexes

Constraints

Migrations

Seed data

---

## Backend

Files changed

Models

Repositories

Services

Routes

Business rules

---

## APIs

Endpoints added

Endpoints updated

Authentication

Permissions

---

## Frontend

Pages

Components

Hooks

Navigation

State management

---

## Validation

Python build

Frontend build

Migration test

API verification

Runtime verification

Known limitations

---

## Remaining Work

List anything not yet implemented.

Never hide incomplete work.

---

# FINAL RULE

Always think like you're shipping software that will be used by thousands of enterprise users.

If a workflow feels incomplete,

do not stop.

Complete it end-to-end.

If a UI exists without a working backend,

it is incomplete.

If an API exists without UI,

it is incomplete.

If both exist but data is not persisted,

it is incomplete.

Only consider work finished when the complete workflow is production-ready.
