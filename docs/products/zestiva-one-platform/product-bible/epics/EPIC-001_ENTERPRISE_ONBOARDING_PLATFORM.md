# EPIC-001 Enterprise Identity, Invitation, Provisioning and Persona-Based Onboarding Platform

Document ID: EPIC-001  
Version: 1.0  
Status: ACTIVE  
Review Frequency: Before each Milestone 2 slice and before onboarding-related implementation  
Owner: Platform Program Office  

---

## 1. Purpose

EPIC-001 defines the enterprise onboarding platform for Zestiva One Platform.

This is not an invitation screen, consultant onboarding flow or UX-only exercise.

It is the reference architecture and product specification for a reusable, metadata-driven onboarding engine that every current and future Zestiva product can inherit.

## 2. Scope

EPIC-001 covers:

- Enterprise invitation.
- Identity creation.
- Provisioning.
- Persona-based onboarding.
- Product selection.
- Organization and workspace selection.
- Department and team assignment.
- Role assignment.
- Permission template assignment.
- Capability bundle assignment.
- Feature flag assignment.
- Communication generation.
- Document requirements.
- Verification.
- Activation.
- Dashboard generation.
- Navigation generation.
- First business outcome.

Application code must not be modified as part of this document.

## 3. Business Mission

Design one reusable onboarding platform capable of onboarding any user into any Zestiva product without architectural redesign.

Current products:

- Nuetra.
- FitEatsy.

Future products:

- Planet.
- CRM.
- HRMS.
- LIMS.
- LMS.
- Marketplace.
- AI Platform.

Products must use the same onboarding engine.

Products must not create isolated onboarding implementations.

## 4. Business Philosophy

Do not design screens first.

Design complete business journeys.

Every screen must exist because it supports a business journey.

Every API must support a workflow.

Every workflow must support a business outcome.

Registration is not success.

Activation is not success.

The onboarding journey ends only after the user successfully performs their first business outcome.

## 5. Primary Journey

```text
Super Admin
  ↓
People & Access
  ↓
Invite User
  ↓
Select Product(s)
  ↓
Select Organization
  ↓
Select Workspace
  ↓
Select Department
  ↓
Select Team
  ↓
Select Persona
  ↓
Assign Role
  ↓
Assign Permission Template
  ↓
Assign Capability Bundle
  ↓
Assign Feature Flags
  ↓
Preview Dashboard
  ↓
Preview Navigation
  ↓
Preview Email / WhatsApp / SMS
  ↓
Schedule or Send Invitation
  ↓
Audit Log
  ↓
Notification
  ↓
Invitation Accepted
  ↓
Identity Created
  ↓
Terms Accepted
  ↓
Security Setup
  ↓
Profile Completion
  ↓
Persona-specific Information
  ↓
Document Upload
  ↓
Verification
  ↓
Approvals
  ↓
Provisioning
  ↓
Dashboard Generated
  ↓
Navigation Generated
  ↓
Activation Checklist
  ↓
Ready
  ↓
First Business Outcome
```

## 6. Supported Personas

The onboarding engine must support:

- Super Admin.
- Platform Admin.
- Organization Admin.
- Workspace Admin.
- Practitioner.
- Nutritionist.
- Mentor.
- Doctor.
- Coach.
- Corporate Wellness Consultant.
- Operations Team.
- Support Team.
- Corporate HR.
- Corporate Manager.
- Employee.
- Patient, future.
- Vendor, future.
- Partner, future.
- System Integration User.
- Future personas.

Every persona uses the same platform engine.

Only persona configuration changes.

## 7. Invitation Platform

Invitation is a reusable platform capability.

It must support:

- Multi-product invitations.
- Multi-organization invitations.
- Multi-workspace invitations.
- Multi-persona invitations.
- Multi-role invitations.
- Permission templates.
- Capability bundles.
- Feature flags.
- Multiple languages.
- Multiple invitation channels.
- Branded invitations.
- Scheduled invitations.
- Invitation expiry.
- Resend.
- Revoke.
- Cancel.
- Reminder strategy.
- Invitation history.
- Invitation audit.

## 8. Identity Platform Rules

Identity is platform-owned.

Identity exists before product access.

Identity is independent from:

- Product.
- Organization.
- Workspace.
- Role.
- Permissions.

Identity supports:

- Email.
- Phone.
- SSO readiness.
- OAuth readiness.
- OIDC readiness.
- MFA readiness.
- Future federation.

## 9. Platform Selection Engine

Product selection must be reusable.

It must support:

- Multiple products.
- Different personas per product.
- Different permissions per product.
- Shared identity.
- Shared dashboards.
- Shared notifications.
- Shared workflows.
- Users belonging to multiple products simultaneously.

## 10. Persona Engine

The Persona Engine determines onboarding requirements from persona configuration.

For every persona define:

- Required profile fields.
- Professional information.
- Required documents.
- Optional documents.
- Verification rules.
- Approval workflow.
- Dashboard.
- Navigation.
- Widgets.
- Capabilities.
- Notifications.
- Activation criteria.
- Business KPIs.

Example persona differences:

| Persona | Example Requirements |
|---|---|
| Practitioner | Registration number, degree, specialization, certificates, consultation types |
| Mentor | Domain expertise, years of experience, coaching categories, certifications |
| Organization Admin | Department, team, administrative scope |
| Employee | Employment profile, organization context, consent |
| Patient, future | Health profile, emergency contact, consent, medical history |

## 11. Provisioning Engine

Provisioning dynamically determines:

- Platform.
- Organization.
- Workspace.
- Department.
- Team.
- Persona.
- Role.
- Permission Template.
- Capability Bundle.
- Feature Flags.
- Dashboard.
- Navigation.
- Widgets.
- Notification Preferences.

Everything must be metadata-driven.

## 12. Onboarding Experience

After invitation acceptance, the user journey is:

```text
Accept Invitation
  ↓
Verify Email / OTP
  ↓
Identity Creation
  ↓
Password / SSO
  ↓
Terms and Privacy
  ↓
Security Setup
  ↓
Profile Completion
  ↓
Professional Information
  ↓
Document Upload
  ↓
Verification
  ↓
Approvals
  ↓
Services Configuration
  ↓
Pricing
  ↓
Availability
  ↓
Calendar Integration
  ↓
Notification Preferences
  ↓
Activation Checklist
  ↓
Dashboard Generated
  ↓
Navigation Generated
  ↓
Ready
  ↓
First Business Outcome
```

The experience must support:

- Progressive disclosure.
- Save and resume.
- Draft state.
- Contextual guidance.
- Validation.
- Recovery.
- Multi-device continuation.
- Mobile-first experience.
- Accessibility.

## 13. Communication Engine

The Communication Engine supports:

- Email.
- WhatsApp.
- SMS.
- Push Notifications.
- In-App Notifications.

Templates must be metadata-driven by:

- Product.
- Organization.
- Workspace.
- Persona.
- Role.
- Language.
- Brand theme.
- Invitation type.
- Country.

## 14. Dynamic Email Generation

Email generation must support:

- Subject generation.
- Header.
- Branding.
- Dynamic sections.
- Responsibilities.
- Required documents.
- Benefits.
- Next steps.
- CTA.
- Support information.
- Legal footer.
- Accessibility.
- Dark mode compatibility.
- Mobile compatibility.

Email templates required:

- Invitation Email.
- Reminder Email.
- Invitation Expiry Email.
- Accepted Email.
- Rejected Email.
- Document Pending Email.
- Document Approved Email.
- Activation Completed Email.

## 15. Document Requirement Engine

Document requirements are dynamic.

Inputs:

- Persona.
- Platform.
- Organization.
- Country.
- State.
- Professional rules.
- Subscription.

Examples:

| Persona | Example Documents |
|---|---|
| Practitioner | Degree, medical registration, PAN, Aadhaar |
| Mentor | Experience certificate, identity proof |
| Nutritionist | Nutrition degree, license |
| Organization Admin | Authorization letter, employee ID |

Supported behavior:

- Conditional documents.
- Optional documents.
- Expiry.
- Renewal.
- Versioning.

## 16. Document Upload Experience

The upload experience must support:

- Drag and drop.
- Camera capture.
- Mobile scan.
- Multiple files.
- Multiple pages.
- Preview.
- OCR readiness.
- Compression.
- Replace.
- Delete.
- Progress.
- Draft.
- Resume.
- Retry.
- Accessibility.

## 17. Verification Engine

Verification must support:

- Automatic verification.
- Manual review.
- AI verification, future.
- Conditional verification.
- Document rejection.
- Re-upload.
- Escalation.
- SLA.
- Audit trail.

## 18. Dashboard and Navigation Generation

Dashboard and navigation must be dynamically generated from:

- Product.
- Persona.
- Organization.
- Workspace.
- Permission Template.
- Capability Bundle.
- Feature Flags.
- Subscription.
- Business Rules.

No dashboard or navigation should be hardcoded by role alone.

## 19. Activation Engine

Activation must define:

- Activation Score.
- Activation Checklist.
- Activation Events.
- Activation KPIs.
- Remaining Steps.
- Readiness Indicator.
- Activation Dashboard.

## 20. First Business Outcome

The onboarding journey completes only after the first successful business outcome.

Examples:

| Persona | First Business Outcome |
|---|---|
| Practitioner | First consultation completed |
| Nutritionist | First nutrition plan published |
| Mentor | First mentoring session completed |
| Doctor | First patient consultation completed |
| Organization Admin | First user invited |
| Corporate HR | First employee onboarded |
| Patient, future | First assessment completed |

## 21. Admin Experience

Administration must support:

- Pending invitations.
- Accepted invitations.
- Expired invitations.
- Rejected invitations.
- Documents pending.
- Verification pending.
- Activated users.
- Inactive users.
- First business outcome pending.
- Bulk actions.
- Audit.
- Reports.

## 22. Workflow State Machines

State machines must be documented for:

- Invitation.
- Identity.
- Documents.
- Verification.
- Provisioning.
- Activation.
- Approvals.
- Notifications.

Every state must define:

- Entry Conditions.
- Exit Conditions.
- Transitions.
- Business Rules.
- Events.
- Notifications.
- Timeouts.
- Escalations.
- Recovery.

## 23. Business Events

Events must support notifications, workflow, analytics, audit, integrations and future AI.

Core events:

- Invitation Created.
- Invitation Sent.
- Invitation Opened.
- Invitation Accepted.
- Invitation Expired.
- Invitation Revoked.
- Identity Created.
- Identity Verified.
- Terms Accepted.
- Security Setup Completed.
- Profile Started.
- Profile Completed.
- Persona Information Completed.
- Documents Uploaded.
- Documents Approved.
- Documents Rejected.
- Provisioning Completed.
- Dashboard Generated.
- Navigation Generated.
- Activation Started.
- Activation Completed.
- First Business Outcome Completed.

## 24. Edge Cases

The platform must handle:

- Invitation expired.
- Invitation revoked.
- Wrong email.
- Existing identity.
- Multiple organizations.
- Multiple workspaces.
- Multiple products.
- Role change during onboarding.
- Duplicate practitioner.
- Document expired.
- Verification rejected.
- Resume onboarding on another device.
- Product disabled during onboarding.
- Permission template changed during onboarding.
- Organization suspended during onboarding.
- Workspace archived during onboarding.

## 25. AI Extension Points

AI is future-facing and must not be required for initial implementation.

Potential extension points:

- OCR.
- Credential validation.
- Duplicate detection.
- Profile quality score.
- Smart reminders.
- Scheduling.
- Fraud detection.
- Document risk scoring.
- Onboarding assistant.

## 26. API Impact

EPIC-001 will require future APIs for:

- Invitation preview.
- Invitation creation.
- Invitation scheduling.
- Invitation resend.
- Invitation revoke.
- Invitation acceptance.
- Persona configuration lookup.
- Product selection lookup.
- Permission template lookup.
- Capability bundle lookup.
- Feature flag assignment.
- Profile onboarding state.
- Document requirements.
- Document upload.
- Verification workflow.
- Provisioning status.
- Activation status.
- Dashboard preview.
- Navigation preview.
- First business outcome tracking.

API contracts must be defined before implementation.

## 27. Database Impact

EPIC-001 will require future data ownership for:

- Invitation provisioning intent.
- Persona configuration.
- Product onboarding rules.
- Capability bundles.
- Permission templates.
- Feature flag assignments.
- Onboarding sessions.
- Onboarding tasks.
- Document requirements.
- Verification decisions.
- Activation checklist.
- First business outcome events.

Database ownership must be defined before implementation.

## 28. Security and Privacy

Security requirements:

- Invitation tokens stored only as secure hashes.
- Invitations scoped to intended identity and access context.
- Persona configuration cannot grant unauthorized access.
- Permission templates require audit.
- Feature flag assignment requires authorization.
- Sensitive documents require secure storage.
- User PII must be protected.
- Multi-tenant boundaries must be enforced.
- Every critical action must be audited.

Privacy requirements:

- Collect only necessary data.
- Explain why documents are required.
- Respect jurisdiction-specific requirements.
- Support future consent management.

## 29. QA Scenarios

QA must validate:

- Each current persona can be invited.
- Future persona can be configured without new onboarding system.
- Multi-product invitation.
- Multi-organization invitation.
- Multi-workspace invitation.
- Expired invitation.
- Revoked invitation.
- Existing identity.
- Document rejection and re-upload.
- Resume on another device.
- Dashboard and navigation generation.
- First business outcome tracking.

## 30. Success Metrics

Business metrics:

- Invitation completion rate.
- Onboarding completion rate.
- Activation rate.
- Time to activation.
- Time to first business outcome.
- Document rejection rate.
- Verification turnaround time.
- Support tickets per onboarding.

Platform metrics:

- Personas onboarded through shared engine.
- Products onboarded through shared engine.
- Percentage of onboarding behavior driven by configuration.
- Duplicate onboarding code avoided.

## 31. Implementation Outputs Required

Before implementation, produce:

- Business Context.
- PRD.
- UX Specification.
- Journey Maps.
- Information Architecture.
- Service Blueprint.
- Workflow Diagrams.
- State Machines.
- Screen Inventory.
- Permission Matrix.
- Capability Matrix.
- Metadata Model.
- Configuration Model.
- Email Specifications.
- Communication Specifications.
- API Impact.
- Database Impact.
- Events.
- Audit Requirements.
- QA Scenarios.
- KPIs.
- Success Metrics.
- Implementation Roadmap.

## 32. Validation Checklist

Before EPIC-001 is considered ready for implementation:

- Supports every current persona.
- Supports future personas.
- Supports multiple products.
- Supports multiple organizations.
- Supports multiple workspaces.
- Configuration is preferred over code.
- No duplicated onboarding logic exists by design.
- Existing platform capabilities are reused.
- Enterprise Meta Model is updated.
- Product Bible is updated.
- ADRs are created if required.
- Document Registry is updated.
- Changelog is updated.

## 33. Inputs

- Product Bible.
- Enterprise Meta Model.
- Zestiva One Platform Blueprint.
- IAM Ecosystem Blueprint.
- Milestone 2 documentation.
- PPO Operating Model.
- ZEPO Operating Model.
- EDO Governance.

## 34. Outputs

- Canonical EPIC-001 scope.
- Metadata-driven onboarding architecture.
- Persona onboarding requirements.
- Future implementation output list.
- Validation checklist.

## 35. Dependencies

- Product Registry.
- Capability Registry.
- Identity Platform.
- Access Platform.
- Organization Platform.
- Workspace Platform.
- Workflow Platform.
- Document Platform.
- Notification Platform.
- Dashboard Engine.
- Navigation Engine.
- Audit Platform.

## 36. Business Rules

- Onboarding is a platform capability, not a product-specific flow.
- Every persona inherits the same onboarding engine.
- Persona-specific behavior is configuration.
- Registration is not success.
- Activation is not the final success measure.
- The journey completes after the first business outcome.
- Product-specific onboarding may extend configuration, not duplicate architecture.

## 37. Related Documents

- `docs/products/zestiva-one-platform/product-bible/README.md`
- `docs/products/zestiva-one-platform/product-bible/APPENDICES/ENTERPRISE_META_MODEL.md`
- `docs/products/zestiva-one-platform/product-bible/APPENDICES/PPO_OPERATING_MODEL.md`
- `docs/architecture/enterprise/ZESTIVA_ONE_PLATFORM_BLUEPRINT.md`
- `docs/milestones/milestone-2-identity-onboarding/IAM_ECOSYSTEM_BLUEPRINT.md`
- `docs/milestones/milestone-2-identity-onboarding/MILESTONE_2_ONBOARDING_WORKFLOW.md`

## 38. Related ADRs

- None at creation.

Recommendation: create ADR-001 when Product Owner approves EPIC-001 as the canonical enterprise onboarding architecture.

