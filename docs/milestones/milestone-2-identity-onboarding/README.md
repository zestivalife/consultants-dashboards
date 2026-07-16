# Milestone 2 – Identity & Onboarding Platform

Version: 1.1

Status: Architecture Review Ready

Owner: Platform Architecture

## Purpose

Milestone 2 creates the reusable Identity & Onboarding Platform for Zestiva LLP products.

The platform must support Nuetra, FitEatsy and future Zestiva products without creating role-specific onboarding implementations.

## Canonical Decisions

- Super Admin is the product-facing name for the platform owner role.
- Identity is generic. No role may own authentication, sessions, password hashing or JWT behavior.
- Onboarding is template-driven. Adding a future role must be configuration-first.
- Slice 1 reuses the existing `user_invitations` table and Owner Console route family.
- Invitation tokens are stored only as secure hashes. Plaintext invitation tokens must never be persisted.
- Notification transport is out of scope for Slice 1. Email and WhatsApp messages are queued as outbox events.
- Slice 1 supports a single product scope per invitation.
- Every mutation must create an audit event.

## Source Of Truth Order Inside This Milestone

1. `README.md`
2. `PRD.md`
3. `TDS.md`
4. `MILESTONE_2_ONBOARDING_WORKFLOW.md`
5. `RBAC_SPECIFICATION.md`
6. `MILESTONE_2_API_SPECIFICATION.md`
7. `MILESTONE_2_DATABASE_DESIGN.md`
8. `MILESTONE_2_UX_SPECIFICATION.md`
9. `NOTIFICATION_SPECIFICATION.md`
10. `AUDIT_LOG_SPECIFICATION.md`
11. `EDGE_CASES.md`
12. `TEST_SCENARIOS.md`
13. `ACCEPTANCE_CRITERIA.md`
14. Existing review and task breakdown documents

If two documents conflict, the higher document in this list wins unless `AGENTS.md` or `PROJECT_STATE.md` says otherwise.

## Existing Canonical Documents

- `PRD.md`
- `TDS.md`
- `MILESTONE_2_IMPLEMENTATION_PLAN.md`
- `MILESTONE_2_ONBOARDING_WORKFLOW.md`
- `MILESTONE_2_API_SPECIFICATION.md`
- `MILESTONE_2_DATABASE_DESIGN.md`
- `MILESTONE_2_UX_SPECIFICATION.md`
- `MILESTONE_2_ARCHITECTURE_REVIEW.md`
- `MILESTONE_2_ENGINEERING_TASK_BREAKDOWN.md`
- `MILESTONE_2_ACCEPTANCE_REVIEW.md`
- `DEPLOYMENT_GUIDELINES.md`
- `ENGINEERING_OPERATING_MANUAL.md`

## Companion Specifications

- `RBAC_SPECIFICATION.md`
- `NOTIFICATION_SPECIFICATION.md`
- `AUDIT_LOG_SPECIFICATION.md`
- `EMAIL_WHATSAPP_TEMPLATES.md`
- `SEQUENCE_DIAGRAMS.md`
- `EDGE_CASES.md`
- `TEST_SCENARIOS.md`
- `ACCEPTANCE_CRITERIA.md`
- `CHANGELOG.md`

## Implementation Slices

1. Invitation Engine
2. Invitation Acceptance
3. Password Setup
4. Authentication & Session
5. Profile Completion
6. Role-Specific Profiles
7. Document Upload & Verification
8. Account Activation & Workspace Resolution

No slice may begin until the preceding slice passes the release checklist.

## Acceptance Rule

Milestone 2 is not accepted until:

- Architecture review passes.
- Every slice is implemented and locally verified.
- Every migration is applied and rollback tested.
- Every API is routed through the gateway.
- Browser runtime verification passes.
- Authentication, session restoration and RBAC regressions pass.
- Audit and notification outbox records are verified.
- Product Owner and Chief Architect approval are recorded.

Final milestone engineering status remains `PLANNED` or `IMPLEMENTATION IN PROGRESS` until implementation and production acceptance evidence exists.
