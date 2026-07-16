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
• ../../PROJECT_STATE.md
• MILESTONE_2_IMPLEMENTATION_PLAN.md
• MILESTONE_2_API_SPECIFICATION.md

---

# Milestone 2 – Changelog

## 2026-07-16

Status: Documentation alignment

Changes:

- Added milestone README and source-of-truth order.
- Added RBAC, notification, audit, template, sequence, edge case, test and acceptance companion specifications.
- Clarified that Super Admin is the product-facing display role for platform owner capabilities.
- Clarified Slice 1 uses existing `user_invitations` and Owner Console invitation APIs.
- Clarified invitation tokens are hash-only and plaintext tokens must never be persisted.
- Clarified notification delivery is out of scope for Slice 1; outbox persistence is required.

Impact:

- No application code changes.
- No database schema changes.
- No deployment changes.

Final Status:

IMPLEMENTED

---

## 2026-07-16

Status: Slice 1 implementation

Commit SHA:

93c2f4bf91514b154bf5179bda62a6ba88580b29

Branch:

develop

Changes:

- Implemented invitation token validation, acceptance, and password setup initiation endpoints for the invitee lifecycle.
- Added hash-only invitation token lookup using `user_invitations.token_hash`; plaintext tokens remain non-persistent.
- Added pending email and WhatsApp invitation outbox events for creation and resend flows.
- Aligned invitation audit actions with the Slice 1 lifecycle events: `INVITATION_CREATED`, `INVITATION_RESENT`, `INVITATION_CANCELLED`, `INVITATION_EXPIRED`, `INVITATION_ACCEPTED`, and `PASSWORD_SETUP_INITIATED`.
- Routed public onboarding invitation endpoints through the API Gateway.
- Added a minimal invite acceptance frontend route without starting profile completion, document upload, or the onboarding wizard.

Summary:

- Slice 1 Invitation Engine now supports secure invitation creation, hash-only token persistence, invite validation, invite acceptance, password setup initiation, resend, cancellation, expiry, email outbox generation, WhatsApp outbox generation, audit logging, RBAC-protected owner actions, API Gateway routing, and a minimal frontend invite acceptance path.

Impact:

- Application code changed in `consultants-dashboards`.
- No database schema changes.
- No authentication, session, JWT, or password hashing implementation changes.

Verification:

- Auth-service People & Access invitation tests passed.
- API Gateway route and permission tests passed.
- Frontend production build passed.

Final Status:

LOCALLY VERIFIED
