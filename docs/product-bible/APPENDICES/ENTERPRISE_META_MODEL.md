# Enterprise Meta Model

Document ID: PRODUCT-BIBLE-META-MODEL  
Version: 1.0  
Status: ACTIVE  
Review Frequency: Monthly and before introducing new domain concepts  
Owner: Enterprise Architecture  

---

## Purpose

The Enterprise Meta Model defines the canonical concepts used across Zestiva One Platform.

Every reusable concept must belong to this model or be added through an approved architecture update.

## Scope

The model applies to all products, services, APIs, workflows, documents, dashboards, navigation, permissions, integrations and AI capabilities.

## Identifier Standard

Every reusable concept receives a permanent identifier.

Identifier examples:

- `CAP-001` for capability.
- `PROD-001` for product.
- `ROLE-001` for role.
- `WF-001` for workflow.
- `ENT-001` for entity.
- `API-001` for API.
- `ADR-001` for architecture decision.
- `PRD-001` for product requirement.
- `DOC-001` for document.

Approved identifiers must not be renamed.

## Canonical Entity Registry

| ID | Concept | Purpose | Owner | Lifecycle |
|---|---|---|---|---|
| ENT-001 | Platform | Root enterprise foundation for all products | Platform Program Office | Active, maintenance, retired |
| ENT-002 | Product | Commercial or operational offering on ZOP | Product Office | Draft, active, suspended, retired |
| ENT-003 | Capability | Reusable business function consumed by products | Capability Owner | Proposed, designed, active, deprecated |
| ENT-004 | Module | Product functional area | Product Owner | Draft, active, hidden, deprecated |
| ENT-005 | Feature | Specific product or module behavior | Product Owner | Draft, flagged, active, retired |
| ENT-006 | Organization | Tenant or customer entity | Organization Platform | Prospect, active, suspended, deactivated |
| ENT-007 | Workspace | Operational scope inside an organization | Workspace Platform | Active, archived, suspended |
| ENT-008 | Department | Organizational subdivision | Organization Platform | Active, inactive |
| ENT-009 | Team | Group of users within an organization or workspace | Organization Platform | Active, inactive |
| ENT-010 | Identity | Authentication identity and credential anchor | Identity Platform | Pending, verified, active, locked, revoked |
| ENT-011 | User | Human or service actor | Identity Platform | Invited, active, suspended, deactivated |
| ENT-012 | Role | Named authority template | Access Platform | Draft, active, deprecated |
| ENT-013 | Permission | Atomic authorization grant | Access Platform | Active, deprecated |
| ENT-014 | Workflow | Stateful business process | Workflow Platform | Draft, active, completed, cancelled |
| ENT-015 | Workflow State | Valid state in a workflow | Workflow Platform | Draft, active, deprecated |
| ENT-016 | Dashboard | Generated operational workspace | Experience Platform | Template, generated, retired |
| ENT-017 | Widget | Reusable dashboard component | Experience Platform | Draft, active, deprecated |
| ENT-018 | Navigation | Generated route/menu structure | Experience Platform | Template, generated, retired |
| ENT-019 | Document | Stored file and metadata | Document Platform | Uploaded, verified, rejected, archived |
| ENT-020 | Document Type | Document requirement template | Document Platform | Draft, active, retired |
| ENT-021 | Verification | Review decision for an entity or document | Workflow Platform | Pending, approved, rejected, expired |
| ENT-022 | Notification | Communication intent or delivery record | Notification Platform | Pending, sent, failed, cancelled |
| ENT-023 | Event | Business or system signal | Platform Services | Created, processed, archived |
| ENT-024 | Integration | External system connection | Integration Platform | Draft, active, failed, disabled |
| ENT-025 | Feature Flag | Runtime feature availability control | Platform Operations | Draft, active, rolled out, retired |
| ENT-026 | Subscription | Commercial entitlement container | Billing Platform | Trial, active, past_due, suspended, cancelled |
| ENT-027 | Billing | Commercial charge and finance domain | Billing Platform | Draft, issued, paid, void |
| ENT-028 | Audit Log | Immutable record of critical action | Audit Platform | Created, retained, exported |
| ENT-029 | AI Agent | AI-enabled automation actor | AI Platform | Draft, active, paused, retired |
| ENT-030 | Settings | Scoped configuration values | Platform Operations | Active, updated, archived |
| ENT-031 | Invitation | Secure onboarding invitation and access intent | Identity Platform | Draft, sent, accepted, expired, revoked |
| ENT-032 | Persona | Business identity archetype that drives onboarding and workspace behavior | Product Office | Proposed, active, deprecated |
| ENT-033 | Permission Template | Reusable permission set assigned during provisioning | Access Platform | Draft, active, deprecated |
| ENT-034 | Capability Bundle | Reusable bundle of platform capabilities assigned to a user context | Capability Owner | Draft, active, deprecated |
| ENT-035 | Onboarding Session | Stateful onboarding journey for an invited or created identity | Onboarding Platform | Draft, in_progress, blocked, completed, abandoned |
| ENT-036 | Activation | Readiness state that confirms a user can operate in a workspace | Onboarding Platform | Not_started, in_progress, ready, completed |
| ENT-037 | First Business Outcome | Persona-specific event that proves onboarding success | Product Office | Pending, completed, failed |

## Capability Identifier Seed

| ID | Capability | Owner |
|---|---|---|
| CAP-001 | Identity | Identity Platform |
| CAP-002 | Access | Access Platform |
| CAP-003 | Organizations | Organization Platform |
| CAP-004 | Workspaces | Workspace Platform |
| CAP-005 | People | People Platform |
| CAP-006 | Invitations | Identity Platform |
| CAP-007 | Provisioning | IAM Platform |
| CAP-008 | Workflow | Workflow Platform |
| CAP-009 | Documents | Document Platform |
| CAP-010 | Verification | Workflow Platform |
| CAP-011 | Notifications | Notification Platform |
| CAP-012 | Communication | Communication Platform |
| CAP-013 | Dashboard | Experience Platform |
| CAP-014 | Navigation | Experience Platform |
| CAP-015 | Search | Data Platform |
| CAP-016 | Reporting | Data Platform |
| CAP-017 | Analytics | Data Platform |
| CAP-018 | Billing | Finance Platform |
| CAP-019 | Subscriptions | Finance Platform |
| CAP-020 | Feature Flags | Platform Operations |
| CAP-021 | Audit | Compliance Platform |
| CAP-022 | Settings | Platform Operations |
| CAP-023 | Developer Platform | Platform Engineering |
| CAP-024 | AI | AI Platform |
| CAP-025 | Integrations | Integration Platform |
| CAP-026 | Onboarding | Onboarding Platform |
| CAP-027 | Persona Engine | Product Office |
| CAP-028 | Activation | Onboarding Platform |

## Product Identifier Seed

| ID | Product | Status |
|---|---|---|
| PROD-001 | Nuetra | Current |
| PROD-002 | FitEatsy | Current |
| PROD-003 | Planet | Planned |
| PROD-004 | CRM | Planned |
| PROD-005 | HRMS | Planned |
| PROD-006 | LIMS | Planned |
| PROD-007 | LMS | Planned |
| PROD-008 | Marketplace | Planned |
| PROD-009 | Telemedicine | Planned |
| PROD-010 | AI Platform | Planned |

## Business Rules

- Every new reusable concept must map to an existing meta-model entity or update this document.
- Product-specific terms must not duplicate platform concepts.
- New identifiers require Product Bible and Document Registry updates where applicable.
- Approved identifiers are permanent.
- Data ownership must be clear before implementation.
- Persona-specific onboarding behavior must be configuration-driven through Persona, Permission Template, Capability Bundle, Onboarding Session and Activation concepts.

## Inputs

- Product Bible.
- Product Registry.
- Capability Registry.
- Architecture documents.
- ADRs.

## Outputs

- Canonical concepts.
- Permanent identifiers.
- Ownership references.
- Consistent terminology.

## Dependencies

- `docs/product-bible/README.md`
- `docs/ZESTIVA_ONE_PLATFORM_BLUEPRINT.md`
- `docs/product-bible/02_BUSINESS_CAPABILITIES.md`
- `docs/product-bible/APPENDICES/GLOSSARY.md`

## Success Metrics

- Fewer duplicated concepts.
- Consistent terminology across docs and implementation.
- Clearer ownership.
- Faster architecture review.
- Better future product extensibility.

## Related Documents

- `docs/product-bible/APPENDICES/PPO_OPERATING_MODEL.md`
- `docs/product-bible/APPENDICES/GLOSSARY.md`
- `docs/ZESTIVA_ONE_PLATFORM_BLUEPRINT.md`

## Related ADRs

- None at creation.
