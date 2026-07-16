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

Status: Slice 3 implementation

Commit SHA:

dc2bb68

Branch:

feature/m2-slice3-credential-creation

Changes:

- Implemented credential creation as a complete vertical slice after invitation acceptance.
- Added a public credential creation API under `/api/v1/identity/password/create`.
- Added secure password policy enforcement with 12-character minimum, uppercase, lowercase, number, special character and common-password checks.
- Added password history persistence and reuse prevention for the last five password hashes.
- Added credential creation audit events for `INVITATION_CONSUMED`, `PASSWORD_CREATED`, `CREDENTIAL_CREATED`, `PASSWORD_VALIDATION_FAILED` and `CREDENTIAL_FAILED`.
- Added pending notification outbox event generation for `PASSWORD_CREATED`.
- Added the `/onboarding/password/setup` frontend route with password strength, policy checklist, confirmation validation, loading, success and terminal invitation states.
- Updated the invitation acceptance page to route accepted invitations into credential creation.
- Routed `/api/v1/identity` through the API Gateway and marked credential creation as a public invitation-token endpoint.

Impact:

- Auth-service credential creation, password policy, password history and invitation lifecycle updated.
- API Gateway routing updated for the new identity endpoint.
- Frontend onboarding invite and password setup routes updated.
- No login, JWT, refresh token, Remember Me, session management, profile completion, document upload, workspace resolution or dashboard loading changes.

Verification:

- Auth-service focused tests passed: `60 passed`.
- API Gateway route tests passed: `5 passed`.
- Python compile check passed for auth-service and api-gateway app modules.
- Auth-service Alembic head verified as `a7b8c9d0e1f2`.
- Frontend production build passed and generated `/onboarding/password/setup`.
- Browser route check passed for `/onboarding/password/setup` invalid-token recovery state with zero console errors.

Final Status:

LOCALLY VERIFIED

---

## 2026-07-16

Status: Slice 2 implementation

Commit SHA:

1c34b530602c45302b07b3407dbfdcc67f584dea

Branch:

feature/m2-slice2-invitation-acceptance

Changes:

- Implemented hash-only invitation validation with explicit expired, revoked, invalid and accepted-token handling.
- Added invitation acceptance lifecycle behavior without starting password creation, profile completion, document upload, workspace loading or dashboard resolution.
- Added organization, product and role validation during validation and acceptance.
- Added Slice 2 audit events for `INVITATION_OPENED`, `INVITATION_ACCEPTED`, `INVITATION_EXPIRED` and `INVITATION_REVOKED`.
- Added pending notification outbox records for invitation acceptance and revocation lifecycle events.
- Updated the invite landing page to render valid, accepted, expired, revoked and invalid invitation states.
- Ensured the invite landing page redirects conceptually to Password Setup through API response metadata while keeping password creation out of scope.

Impact:

- Auth-service invitation lifecycle logic updated.
- Public onboarding validation route now records request metadata.
- Frontend invite route updated.
- No authentication, session, JWT, password hashing, profile completion, document upload or workspace loading changes.
- No database schema changes.

Verification:

- Auth-service People & Access invitation tests passed.
- API Gateway onboarding route tests passed.
- Frontend production build passed.

Final Status:

LOCALLY VERIFIED

---

## 2026-07-16

Status: Slice ordering alignment

Branch:

develop

Changes:

- Updated Milestone 2 Slice 2 to `Invitation Acceptance`.
- Moved `Password Setup` to Slice 3.
- Moved `Authentication & Session` to Slice 4.
- Moved `Profile Completion` to Slice 5.
- Moved `Role-Specific Profiles` to Slice 6.
- Moved `Document Upload & Verification` to Slice 7.
- Moved `Account Activation & Workspace Resolution` to Slice 8.
- Clarified that Slice 2 excludes password creation, profile completion, document upload, workspace loading and dashboard resolution.

Impact:

- Documentation alignment only.
- No application code changes.
- No database schema changes.
- No deployment changes.

Final Status:

IMPLEMENTED

---

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
