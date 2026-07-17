# IAM Ecosystem Blueprint

Version: 1.0

Status: Architecture Approved for Implementation Planning

Owner: Platform Architecture

Related Documents:

- `README.md`
- `PRD.md`
- `TDS.md`
- `MILESTONE_2_ONBOARDING_WORKFLOW.md`
- `MILESTONE_2_UX_SPECIFICATION.md`
- `MILESTONE_2_API_SPECIFICATION.md`
- `MILESTONE_2_DATABASE_DESIGN.md`
- `RBAC_SPECIFICATION.md`
- `NOTIFICATION_SPECIFICATION.md`
- `AUDIT_LOG_SPECIFICATION.md`
- `EMAIL_WHATSAPP_TEMPLATES.md`
- `ACCEPTANCE_CRITERIA.md`

---

## 1. Purpose

This document defines the enterprise Identity and Access Management ecosystem for Zestiva.

The platform must support Nuetra, FitEatsy, and unlimited future products without redesigning authentication, onboarding, authorization, navigation, or dashboard provisioning.

This document does not replace the existing milestone specifications. It binds them together into one access-context architecture.

---

## 2. Core Principle

The system shall be a single enterprise application.

There shall be:

- One authentication system
- One login page
- One identity service
- One session management system
- One routing system
- One design system
- One navigation framework
- One onboarding engine

User experience differs by access context, not by separate applications.

Dashboard provisioning must never be decided by role alone.

Dashboard context is resolved from:

- Product
- Organization
- Workspace
- Role
- Permission set
- Feature flags
- Subscription plan
- Business rules
- User assignments
- Policy context

---

## 3. Access Context Resolution

Every authenticated user resolves through the following chain:

```text
Authentication
↓
Identity
↓
Organization
↓
Workspace
↓
Role
↓
Permission Set
↓
Feature Flags
↓
Subscription Plan
↓
Dashboard Provisioning
↓
Navigation Generation
↓
User Experience
```

The output of this resolution is an `access_context`.

The `access_context` determines:

- Default dashboard
- Available navigation
- Allowed routes
- Allowed actions
- Data scope
- Feature visibility
- Workspace switcher options
- Product switcher options
- Invitation templates
- Onboarding templates
- Required documents
- Approval rules

---

## 4. IAM Domains

### Authentication

Authentication verifies the user identity.

It must remain generic and identical for every user type.

Authentication owns:

- Login
- Password verification
- Refresh token flow
- Session creation
- Session revocation
- Logout
- Account lock checks

Authentication must not own:

- Dashboard selection
- Role-specific routing
- Business profile logic
- Product-specific onboarding

### Identity

Identity represents the person or service account.

Identity owns:

- User record
- Account status
- Verification status
- Credential status
- Role assignments
- Organization memberships
- Product access
- Workspace access

### Authorization

Authorization evaluates what the authenticated identity may do.

Authorization must use RBAC plus ABAC.

RBAC evaluates:

- Role
- Permission set
- Permission template
- Permission override

ABAC evaluates:

- Product
- Organization
- Workspace
- Department
- Subscription
- Feature flag
- Policy
- Context
- Assignment

### Provisioning

Provisioning converts access context into a usable workspace experience.

Provisioning owns:

- Dashboard destination
- Navigation tree
- Module visibility
- Landing page
- First-run onboarding destination
- Product workspace selection
- Organization workspace selection

---

## 5. Invitation Workflow Architecture

The invitation workflow must create an enterprise provisioning intent, not merely an email.

### Step 1: Select Member Type

Supported examples:

- Doctor
- Consultant
- Practitioner
- Nutritionist
- Mentor
- Corporate Admin
- Organization Admin
- Platform Admin
- Finance
- Operations
- Sales
- Support
- Developer
- Auditor
- Future configurable roles

The selected member type determines:

- Available role templates
- Available permission templates
- Required organization scope
- Required workspace scope
- Required onboarding template
- Required document template
- Approval workflow

### Step 2: Member Information

Required fields:

- First name
- Last name
- Email
- Mobile number
- Country
- Timezone
- Language
- Preferred communication channel

### Step 3: Platform Selection

Platform selection must use product cards.

Supported choices:

- Nuetra
- FitEatsy
- Both platforms
- Future products

Platform selection dynamically controls all remaining steps.

Slice-level note:

Current Slice 3 UI may remain single-product where backend support is single-product. The architecture must not block multi-product invitation support in a future slice.

### Step 4: Organization

The inviter may:

- Search an existing organization
- Create a new organization
- Assign a single organization
- Assign multiple organizations where supported
- Assign enterprise group context where supported

Organization assignment must be validated before invitation send.

### Step 5: Workspace

The inviter may:

- Search an existing workspace
- Create a workspace
- Assign department
- Assign branch
- Assign clinic
- Assign corporate unit
- Assign region
- Assign project workspace
- Use future workspace types

Workspace assignment must be product and organization scoped.

### Step 6: Access Control

The UI label must be `Access Control` or `Access Scope`.

Do not use `Services & Packages` as the primary IAM step name.

Access control supports:

- Modules
- Permissions
- CRUD rights
- Reports
- Analytics
- Patients or clients
- Corporate features
- Marketplace
- Assessments
- Nutrition
- Finance
- HR
- Administration
- Future modules
- Permission templates
- Permission overrides
- Custom permissions

### Step 7: Review

The review screen must display a complete provisioning summary:

- Member
- Product or platform
- Organization
- Workspace
- Role
- Permission set
- Feature flags
- Subscription
- Generated dashboard
- Generated navigation
- Generated login destination
- Generated landing page
- Generated access matrix
- Required onboarding steps
- Required documents
- Approval workflow

### Step 8: Email Preview

The system generates the invitation content automatically.

Administrators may review the generated content but must not be required to write invitation emails manually.

The message must be professional, trustworthy, and security-aware.

Canonical subject:

```text
Welcome to Zestiva
```

Canonical body intent:

```text
Hello {{FirstName}},

Welcome to the Zestiva ecosystem.

You have been invited to join {{Platform}} as {{Role}} for {{Organization}} / {{Workspace}}.

During onboarding you will securely verify your identity, create your password, configure your profile, complete professional information, and upload required verification documents through the secure onboarding portal.

Never send sensitive documents by email.

This invitation expires after {{ExpiryWindow}}.
```

Primary actions:

- Start secure onboarding
- Need help
- Contact support

### Step 9: Send Invitation

Supported channels:

- Email
- WhatsApp
- Copy link
- SMS, future
- QR code, future

If email or WhatsApp providers are unavailable, the workflow must remain testable through copy link and open link actions.

### Step 10: Success

Success screen actions:

- Copy invitation link
- Open invitation link
- Resend email
- Send WhatsApp
- Invite another member
- Done

---

## 6. Member Onboarding Journey

Canonical member journey:

```text
Invitation Link
↓
Email Verification
↓
Mobile Verification, optional
↓
Password Creation
↓
Terms Acceptance
↓
Profile Setup
↓
Professional Information
↓
Document Upload
↓
Verification
↓
Approval Workflow
↓
Dashboard Provisioning
↓
First Login
```

Each step must be resumable and auditable.

No future slice may require a separate login page for a new user type.

---

## 7. Document Management Architecture

Document requirements must be configurable by:

- Product
- Organization
- Workspace
- Member type
- Role
- Country
- Regulatory policy
- Business policy

Supported document examples:

- Aadhaar
- PAN
- Educational degrees
- Professional certificates
- Medical council registration
- Professional license
- GST
- Address proof
- Passport
- Driving license
- Cancelled cheque
- Profile photograph
- Organization-specific documents
- Future document types

Each document supports:

- Upload
- Preview
- Replace
- Delete
- OCR readiness
- AI validation readiness
- Manual verification
- Expiry tracking
- Status tracking
- Audit history

Sensitive documents must never be requested or collected through email.

---

## 8. Dashboard Provisioning Engine

Dashboard generation is a provisioning decision, not a role switch.

The engine evaluates:

- Identity status
- Credential status
- Invitation status
- Onboarding status
- Product access
- Organization memberships
- Workspace memberships
- Role assignments
- Permission sets
- Feature flags
- Subscription plan
- Licensed modules
- Business policies
- Approval status

Example outcomes:

| User Context | Provisioned Destination |
|---|---|
| Super Admin with global platform access | Platform Console |
| Corporate Admin with employee analytics license | Corporate Dashboard |
| Organization Admin with people management permissions | Organization Console |
| Doctor with clinical module access | Clinical Dashboard |
| Nutritionist with nutrition module access | Nutrition Dashboard |
| Consultant assigned clients | Consultant Workspace |
| Mentor assigned practitioners | Mentor Console |
| Finance with billing module access | Finance Dashboard |
| Sales with CRM module access | CRM Dashboard |
| Support with ticket module access | Support Console |
| Future patient user | Patient Portal |

When multiple destinations are valid, the workspace resolver must choose the highest-priority active workspace and expose a switcher where authorized.

---

## 9. Dynamic Navigation Engine

Navigation must be generated dynamically.

Navigation input:

- Product
- Organization
- Workspace
- Role
- Permission set
- Feature flags
- Subscription
- Business rules

Navigation output:

- Sidebar items
- Header actions
- Quick actions
- Route availability
- Empty state actions
- Contextual action menus
- Keyboard command palette entries

Navigation must not be hardcoded by role.

Frontend route hiding is not security. Backend authorization remains mandatory.

---

## 10. Database Architecture Additions

The existing canonical database design remains valid.

Future implementation slices must support these logical entities without role-specific authentication tables:

- products
- product_modules
- feature_flags
- subscriptions
- subscription_modules
- organizations
- organization_groups
- workspaces
- workspace_memberships
- role_templates
- permission_templates
- permission_overrides
- access_policies
- access_context_snapshots
- dashboard_templates
- navigation_templates
- invitation_provisioning_intents
- onboarding_template_requirements
- document_requirement_templates
- notification_templates

Implementation rule:

Do not create Doctor, Consultant, Mentor, or Corporate Admin authentication tables. Role-specific business profiles may exist only outside authentication and must reference the generic identity.

---

## 11. API Architecture Additions

The API surface must support access-context-driven provisioning.

Future endpoint families:

```text
GET  /api/v1/identity/access-context
GET  /api/v1/identity/navigation
GET  /api/v1/identity/dashboard-destination
POST /api/v1/owner/people-access/invitations/preview
POST /api/v1/owner/people-access/invitations/provisioning-summary
GET  /api/v1/owner/people-access/permission-templates
GET  /api/v1/owner/people-access/member-types
GET  /api/v1/owner/people-access/document-requirements
```

Existing Slice 1-3 APIs remain canonical until a documented migration changes them.

Every mutation must:

- Enforce RBAC and ABAC
- Validate organization scope
- Validate workspace scope
- Validate product scope
- Persist audit events
- Persist notification outbox events where applicable
- Return a correlation ID

---

## 12. State Machines

### Invitation State

```text
DRAFT
↓
PENDING
↓
VIEWED
↓
ACCEPTED
↓
CREDENTIAL_CREATED
↓
ONBOARDING_STARTED
↓
ONBOARDING_SUBMITTED
↓
APPROVED
↓
ACTIVATED
```

Terminal or alternate states:

- EXPIRED
- REVOKED
- CANCELLED
- REJECTED
- LOCKED

### Credential State

```text
NOT_CREATED
↓
POLICY_VALIDATED
↓
CREATED
↓
ACTIVE
```

Alternate states:

- FAILED_POLICY
- COMPROMISED
- RESET_REQUIRED
- LOCKED

### Provisioning State

```text
NOT_READY
↓
ACCESS_CONTEXT_READY
↓
NAVIGATION_READY
↓
DASHBOARD_READY
↓
ACTIVE
```

Alternate states:

- BLOCKED_BY_APPROVAL
- BLOCKED_BY_SUBSCRIPTION
- BLOCKED_BY_DOCUMENTS
- BLOCKED_BY_POLICY

---

## 13. Notification Architecture

Notification events must be generated through an outbox pattern.

Transport channels:

- Email
- WhatsApp
- In-app
- SMS, future
- Push, future

Invitation notifications:

- INVITATION_CREATED
- INVITATION_PREVIEW_GENERATED
- INVITATION_SENT
- INVITATION_RESENT
- INVITATION_REVOKED
- INVITATION_EXPIRED
- INVITATION_ACCEPTED
- CREDENTIAL_CREATED
- ONBOARDING_STARTED
- ONBOARDING_SUBMITTED
- ONBOARDING_APPROVED
- ACCOUNT_ACTIVATED

Transport failure must not corrupt identity or invitation state.

---

## 14. Audit Architecture

Every IAM mutation must generate an audit event.

Audit payload should include:

- Actor
- Target identity
- Target organization
- Target workspace
- Product
- Action
- Old value
- New value
- Permission evaluated
- Access policy evaluated
- IP address
- User agent
- Request ID
- Correlation ID
- Timestamp

Audit events must be immutable.

---

## 15. Security Model

Mandatory controls:

- Single login page
- Secure password hashing through the shared password service
- Invitation tokens stored only as secure hashes
- Plaintext tokens displayed only at creation/regeneration time
- Token expiry
- Token revocation
- Replay prevention
- Organization and workspace validation
- RBAC plus ABAC enforcement
- Backend authorization on every protected route
- No sensitive documents by email
- No role-specific auth forks
- No dashboard routing by role alone
- Audit for every mutation
- Rate limits for invitation and credential endpoints
- Correlation IDs on all IAM requests

---

## 16. Frontend Component Hierarchy

Reusable IAM components:

- IAMWorkspaceShell
- AccessContextProvider
- DynamicNavigationRenderer
- DashboardDestinationResolver
- InvitationWizard
- MemberTypeSelector
- ProductCardSelector
- OrganizationSelector
- WorkspaceSelector
- AccessControlBuilder
- ProvisioningSummary
- EmailPreview
- InvitationSuccessPanel
- DocumentRequirementList
- OnboardingProgressTracker
- PolicyAwareActionButton

Components must be reusable across Nuetra, FitEatsy, and future products.

Business rules must not live inside React components.

---

## 17. QA Checklist

Acceptance testing must verify:

- One login page serves every supported role.
- Invitation wizard dynamically changes by selected platform.
- Product cards are selectable.
- Organization search and creation paths are available where in scope.
- Workspace search and creation paths are available where in scope.
- Access Control displays modules, permissions, templates, and overrides where available.
- Review screen displays generated dashboard, navigation, landing page, and access matrix.
- Email preview renders generated content.
- Copy link works when providers are unavailable.
- Open link completes the invitee path.
- Backend rejects unauthorized invitation actions.
- Audit events exist for every mutation.
- Notification outbox events exist for every notification-worthy action.
- Dashboard destination is not role-only.
- Navigation is not hardcoded by role.
- Browser refresh preserves workflow state where the slice requires it.
- WCAG AA keyboard and screen reader basics pass.

---

## 18. Acceptance Criteria

The IAM ecosystem is acceptable only when:

- New products can be added without redesigning onboarding.
- New member types can be added through configuration-first role and onboarding templates.
- Invitation creation produces a complete provisioning intent.
- Invitation acceptance connects to credential creation.
- Credential creation connects to onboarding.
- Onboarding connects to approval.
- Approval connects to dashboard provisioning.
- Dashboard provisioning uses full access context.
- Navigation generation uses full access context.
- Every mutation is audited.
- Notification events are persisted.
- No sensitive token or document data is exposed insecurely.
- The Product Owner can demonstrate the workflow through the deployed UI.

---

## 19. Engineering Task Breakdown

Implementation must proceed in approved vertical slices.

Recommended order:

1. Invitation wizard access-context UX alignment
2. Invitation provisioning summary API
3. Invitation email preview generation
4. Permission template API
5. Access-context resolver API
6. Dynamic navigation resolver API
7. Dashboard destination resolver API
8. Document requirement template engine
9. Onboarding profile and document slices
10. Account activation and workspace resolution

No slice may begin until dependencies are documented and Product Owner approval is recorded.
