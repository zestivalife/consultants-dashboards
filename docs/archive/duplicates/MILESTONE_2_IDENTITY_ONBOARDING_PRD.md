# Milestone 2 PRD: Identity & Onboarding Platform

## Document Control

| Field | Value |
| --- | --- |
| Product | Zestiva Enterprise Platform |
| Company | Zestiva LLP |
| Products Supported | Nuetra, FitEatsy, future Zestiva products |
| Milestone | Milestone 2: Identity & Onboarding Platform |
| Document Type | Product Requirement Document |
| Status | Draft for Review |
| Implementation Status | Not Started |
| Last Updated | 2026-07-14 |

## 1. Objective

Build a reusable, template-driven onboarding platform for every workforce and enterprise user type in the Zestiva ecosystem.

The platform must support:

- Practitioner
- Mentor
- Consultant
- Organization Admin
- Corporate Admin
- Future configurable roles

The platform must not create role-specific onboarding implementations. Roles consume onboarding templates, policy rules, permission scopes, document requirements, approval steps, notification events, and activation rules from configuration.

## 2. Background

Zestiva is moving from product-specific workflows toward a shared enterprise platform. Nuetra and FitEatsy must use the same identity, invitation, onboarding, approval, activation, and audit foundations.

Current product modules should not own onboarding logic. Onboarding is a platform capability that business modules consume.

## 3. Business Goals

1. Create one reusable onboarding engine for all current and future user categories.
2. Reduce duplicate workflows across Nuetra, FitEatsy, organizations, practitioners, mentors, and consultants.
3. Support enterprise-grade governance with approvals, audit trails, document review, and permission-scoped activation.
4. Allow Platform Owners to configure onboarding templates without engineering new role-specific flows.
5. Support product-aware and organization-aware onboarding across Nuetra, FitEatsy, and future products.
6. Ensure authentication remains role-neutral. Onboarding config may vary by role, but login/session behavior must remain identical for all users.

## 4. Non-Goals

This milestone does not implement:

- A new login architecture.
- JWT redesign.
- Refresh token redesign.
- Password service redesign.
- Product-specific practitioner onboarding hardcoded into business modules.
- Role-specific frontend pages for every role.
- Public self-registration unless enabled by a future template policy.
- Payment, subscription, or package purchase workflows.

## 5. Users and Stakeholders

| Stakeholder | Needs |
| --- | --- |
| Platform Owner | Configure onboarding templates, approve users, audit onboarding progress, manage exceptions. |
| Organization Admin | Invite organization users and track onboarding where permitted. |
| Corporate Admin | Invite employees and business users based on organization policy. |
| Practitioner | Complete profile, upload documents, submit for review, become active. |
| Mentor | Complete profile and availability, submit required documents, become active. |
| Consultant | Complete profile, credentials, service/product scope, become active. |
| Future Role | Use configurable templates without new role-specific code. |
| Compliance / Operations | Review identity lifecycle, document history, approvals, and activation evidence. |

## 6. Product Principles

1. Role-neutral identity.
2. Template-driven onboarding.
3. Product-aware and organization-aware scoping.
4. Server-side permissions and lifecycle enforcement.
5. Audit every state transition.
6. Every user has exactly one identity record.
7. Role-specific profile data belongs in role profile extensions, not the `users` table.
8. Every onboarding workflow is resumable.
9. Every approval or rejection has a reason and actor.
10. Every email link expires and is single-purpose.

## 7. Core Workflow

The canonical onboarding lifecycle is:

```text
Invitation
↓
Email
↓
Verification
↓
Password
↓
Profile
↓
Documents
↓
Approval
↓
Activation
↓
Login
```

Templates may skip or reorder non-security steps only when explicitly allowed by policy. Security-sensitive steps must preserve required order:

```text
Invitation / eligibility → email verification → password setup → activation eligibility → login
```

## 8. Template-Driven Onboarding

An onboarding template defines:

- Template key and version.
- Supported role types.
- Supported product scopes.
- Supported organization scopes.
- Required steps.
- Optional steps.
- Step order.
- Required fields.
- Required documents.
- Approval rules.
- Expiry rules.
- Notification rules.
- Permission grants on activation.
- Rejection and rework rules.
- Resume behavior.
- Audit requirements.

Templates must support future roles through configuration:

```text
Role
↓
Template Assignment
↓
Step Definition
↓
Field Definition
↓
Document Definition
↓
Approval Policy
↓
Activation Policy
```

## 9. Role-Neutral Onboarding Examples

These are configuration examples, not separate implementations.

| Role | Template Variation |
| --- | --- |
| Practitioner | Professional profile, qualifications, license documents, approval required. |
| Mentor | Coaching profile, availability, program scope, approval required. |
| Consultant | Specialization, availability, communication channels, approval required. |
| Organization Admin | Organization assignment, authority scope, approval optional. |
| Corporate Admin | Corporate account assignment, employee management permissions, approval optional. |
| Future Role | Configurable profile sections, documents, approval policy, activation policy. |

## 10. Functional Requirements

### 10.1 Template Management

Platform Owners must be able to define and manage onboarding templates.

Required capabilities:

- Create template.
- Version template.
- Activate template.
- Retire template.
- Assign template to role/product/organization scope.
- Define ordered steps.
- Define required and optional fields.
- Define document requirements.
- Define approval policies.
- Define notifications.
- Define activation conditions.
- Preview template as an end user.

### 10.2 Invitation

The platform must support invitation-based onboarding.

Required capabilities:

- Create invitation.
- Assign role.
- Assign product scope.
- Assign organization scope.
- Assign onboarding template.
- Set expiration.
- Send invite email.
- Resend invite.
- Cancel invite.
- Track invitation status.
- Prevent duplicate active invitations for the same email, role, product, and organization scope unless explicitly allowed.

Invitation statuses:

- `draft`
- `sent`
- `opened`
- `accepted`
- `expired`
- `cancelled`
- `revoked`

### 10.3 Email Verification

The platform must verify invited users before password setup.

Required capabilities:

- Single-purpose verification token.
- Token expiration.
- Token revocation.
- Token replay prevention.
- Verification event audit.

### 10.4 Password Setup

The platform must use the shared PasswordService.

Required capabilities:

- Password complexity validation.
- Shared password hashing only.
- No duplicate hashing logic.
- Password setup token validation.
- Password setup completion audit.

### 10.5 Profile Completion

The onboarding engine must render profile forms based on template fields.

Required capabilities:

- Dynamic field groups.
- Required and optional fields.
- Field validation.
- Draft save.
- Resume later.
- Product-scoped fields.
- Organization-scoped fields.
- Role-profile mapping without hardcoded role pages.

### 10.6 Document Collection

The engine must support document requirements defined by template.

Required capabilities:

- Upload required documents.
- Validate file type and size.
- Store document metadata.
- Track review status.
- Support replacement after rejection.
- Preserve document history.
- Enforce access control.

Document statuses:

- `required`
- `uploaded`
- `under_review`
- `approved`
- `rejected`
- `expired`
- `replaced`

### 10.7 Approval

Templates define whether approval is required.

Required capabilities:

- Approve onboarding.
- Reject onboarding.
- Request changes.
- Assign reviewer.
- Track reviewer notes.
- Track approval SLA.
- Escalate overdue approvals.
- Audit every decision.

Approval statuses:

- `not_required`
- `pending`
- `changes_requested`
- `approved`
- `rejected`

### 10.8 Activation

Activation occurs only when all template-defined requirements are satisfied.

Required capabilities:

- Validate email verification.
- Validate password setup.
- Validate required profile sections.
- Validate required documents.
- Validate approval policy.
- Assign product scopes.
- Assign organization scopes.
- Assign permission bundles.
- Mark user active.
- Emit activation events.

### 10.9 Login

After activation, the user logs in through the existing shared authentication flow. Login must not vary by role.

## 11. UX Requirements

### 11.1 Platform Owner UX

Platform Owners need an operational console for onboarding.

Required views:

- Onboarding Templates.
- Invitations.
- Onboarding Runs.
- Approval Queue.
- Document Review Queue.
- Exceptions.
- Audit Timeline.
- Template Preview.

### 11.2 Invited User UX

Invited users need a clear guided flow.

Required experience:

- Secure invitation landing page.
- Progress indicator.
- Step-by-step onboarding wizard.
- Save and resume.
- Inline validation.
- Document upload feedback.
- Approval status.
- Rework instructions if rejected.
- Activation confirmation.

### 11.3 Enterprise UX Standards

- Route-backed steps.
- Deep links for reviewer queues.
- Accessible forms.
- WCAG 2.2 AA.
- Explicit loading states.
- Actionable error states.
- No dead buttons.
- No mock production data.

## 12. Permission Matrix

Permissions must be capability-based, not role-name based.

| Permission | Purpose |
| --- | --- |
| `onboarding.templates.read` | View onboarding templates. |
| `onboarding.templates.create` | Create templates. |
| `onboarding.templates.edit` | Edit draft templates. |
| `onboarding.templates.publish` | Publish template versions. |
| `onboarding.templates.retire` | Retire templates. |
| `onboarding.invitations.read` | View invitations. |
| `onboarding.invitations.create` | Create invitations. |
| `onboarding.invitations.cancel` | Cancel invitations. |
| `onboarding.invitations.resend` | Resend invitations. |
| `onboarding.runs.read` | View onboarding runs. |
| `onboarding.runs.manage` | Manage onboarding runs. |
| `onboarding.documents.read` | View submitted documents. |
| `onboarding.documents.review` | Approve or reject documents. |
| `onboarding.approvals.read` | View approval queue. |
| `onboarding.approvals.decide` | Approve, reject, or request changes. |
| `onboarding.activation.execute` | Activate eligible users. |
| `onboarding.audit.read` | View onboarding audit events. |

## 13. Notification Events

The platform must emit events for:

- Invitation created.
- Invitation sent.
- Invitation opened.
- Invitation accepted.
- Invitation expiring soon.
- Invitation expired.
- Email verified.
- Password setup completed.
- Profile step completed.
- Document uploaded.
- Document rejected.
- Document approved.
- Approval requested.
- Approval assigned.
- Changes requested.
- Onboarding approved.
- Onboarding rejected.
- User activated.
- Activation failed.

## 14. Audit Events

Every lifecycle change must produce an audit event.

Required audit dimensions:

- Actor.
- Target user.
- Target invitation.
- Target onboarding run.
- Action.
- Previous state.
- New state.
- Timestamp.
- IP address.
- Browser / user agent.
- Request ID.
- Product scope.
- Organization scope.

## 15. Reporting Requirements

Platform Owners need visibility into:

- Invitations sent.
- Invitation acceptance rate.
- Onboarding completion rate.
- Average time to activation.
- Approval backlog.
- Document rejection rate.
- Role/product/organization breakdown.
- Stalled onboarding runs.
- Expiring invitations.

## 16. Error Handling Requirements

The user experience must provide clear, actionable errors for:

- Expired invitation link.
- Cancelled invitation.
- Already accepted invitation.
- Invalid verification token.
- Password policy failure.
- Required field missing.
- Invalid document type.
- File too large.
- Approval rejected.
- Permission denied.
- Organization scope invalid.
- Product scope invalid.

## 17. Security Requirements

- Invite tokens must be single-purpose and expire.
- Verification tokens must be single-purpose and expire.
- Password setup must use shared PasswordService.
- Document access must be permission-scoped.
- Sensitive fields must never be logged.
- All mutations require audit logs.
- Onboarding APIs must enforce server-side authorization.
- Activation must be transactional.
- Users cannot self-assign permissions.

## 18. Acceptance Criteria

Architecture approval requires:

- Role-neutral onboarding model.
- Template-driven workflow.
- Product and organization scoping.
- Security model aligned with existing identity rules.
- Database design reviewed.
- API contracts reviewed.
- UX flows reviewed.
- State machines reviewed.
- Permission matrix reviewed.
- No implementation before approval.

Implementation acceptance, in a future milestone, will require:

- Migration applied.
- APIs working.
- Frontend connected.
- Onboarding templates persisted.
- Invitations persisted.
- Documents persisted.
- Approvals persisted.
- Audit events created.
- Notifications emitted.
- Runtime verified in production.

## 19. Open Questions

1. Which roles require MFA at activation or first login?
2. Should organization admins be allowed to invite consultants, or only internal organization users?
3. Should document review be centralized to Platform Owners or delegable to senior consultants/admins?
4. What file storage provider will be approved for production documents?
5. What SLA thresholds should trigger onboarding escalation?
6. Should future self-registration be supported as a template mode?

## 20. Recommendation

Approve a reusable onboarding platform with:

- Template-driven workflows.
- State-machine-controlled onboarding runs.
- Product/organization scoped permissions.
- Dedicated document and approval subsystems.
- Notification and audit event emission.
- No role-specific onboarding implementations.

