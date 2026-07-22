# 02 Business Capabilities

Document ID: PRODUCT-BIBLE-02  
Version: 1.0  
Status: PHASE 1 COMPLETE  
Lifecycle: LIVING PRODUCT AUTHORITY  
Owner: Zestiva Enterprise Product Office  
Last Updated: 17 July 2026

---

## Purpose

This document defines the initial Zestiva One Platform capability map.

Capabilities are reusable business building blocks consumed by Nuetra, FitEatsy and future products.

Products must consume capabilities instead of reimplementing them independently.

---

## Capability Layers

```text
Business Layer
  ↓
Product Layer
  ↓
Capability Layer
  ↓
Platform Services
  ↓
Infrastructure Layer
  ↓
Cloud
```

Business capabilities sit between product strategy and technical services.

---

## Capability Registry

| Capability | Purpose | Platform Owner | Consumed By |
|---|---|---|---|
| Identity | Establish user identity and credentials | Identity Platform | All products |
| Access | Determine effective permissions | IAM Platform | All products |
| Organizations | Manage customer and internal tenants | Organization Platform | All products |
| Workspaces | Scope operational units inside organizations | Workspace Platform | All products |
| People | Manage users and members | People Platform | All products |
| Invitations | Invite users into scoped access contexts | Identity Platform | All products |
| Provisioning | Convert intent into assignments and access | IAM Platform | All products |
| Onboarding | Orchestrate persona-based onboarding journeys | Onboarding Platform | All products |
| Persona Engine | Resolve persona-specific requirements and workflows | Product Office | All products |
| Workflow | Execute stateful business processes | Workflow Platform | All products |
| Documents | Store and manage documents | Document Platform | Product workflows |
| Verification | Review documents and approvals | Workflow Platform | Product workflows |
| Notifications | Route communication events | Notification Platform | All products |
| Communication | Manage channels and templates | Communication Platform | All products |
| Activation | Track readiness and first business outcome | Onboarding Platform | All products |
| Dashboard | Generate dashboards by access context | Experience Platform | All products |
| Navigation | Generate menus and routes dynamically | Experience Platform | All products |
| Widgets | Reusable dashboard components | Experience Platform | All products |
| Analytics | Product and platform intelligence | Data Platform | All products |
| Reporting | Operational reports and exports | Data Platform | All products |
| Billing | Invoice and payment operations | Finance Platform | Commercial products |
| Subscriptions | Entitlements and licensing | Finance Platform | Commercial products |
| Payments | Payment provider integrations | Finance Platform | Commercial products |
| Search | Permission-aware search | Data Platform | All products |
| Settings | Scoped platform configuration | Platform Operations | All products |
| Audit | Immutable business action records | Compliance Platform | All products |
| Developer Platform | APIs, SDKs and integration tooling | Platform Engineering | Partners and internal teams |
| AI | AI agents, tools and governance | AI Platform | AI-enabled products |
| Integrations | External system connectivity | Integration Platform | All products |

---

## Capability Ownership Rules

- Every capability has a clear owner.
- Every capability has an API contract before production implementation.
- Every capability has audit expectations where business critical.
- Every capability has security boundaries.
- Every capability has test coverage requirements.
- Products consume capabilities through APIs or approved internal contracts.

---

## Capability Reuse Rules

Products must not duplicate these capabilities:

- Authentication.
- Authorization.
- Invitations.
- Onboarding.
- Organization management.
- Workspace management.
- Permission management.
- Notification routing.
- Document storage.
- Workflow execution.
- Audit logging.
- Navigation generation.
- Dashboard generation.
- Billing entitlement logic.

If a product needs different behavior, it must request configuration or extension of the shared capability.

---

## Product Registry Relationship

Each product declares:

- Modules.
- Capabilities used.
- Navigation.
- Dashboard.
- Permissions.
- Widgets.
- Feature flags.
- Notifications.
- Document requirements.
- Workflows.

The Product Registry maps product configuration to platform capabilities.

---

## Capability Maturity Model

| Level | Meaning |
|---|---|
| L0 Concept | Business need identified |
| L1 Designed | Requirements and architecture documented |
| L2 Implemented | Backend and frontend exist |
| L3 Locally Verified | End-to-end local workflow verified |
| L4 Production Verified | Runtime production verification passed |
| L5 Enterprise Ready | Observability, scale, security and support mature |

---

## Initial Capability Maturity

| Capability | Current Maturity | Notes |
|---|---|---|
| Identity | L2 Implemented | Stabilization continues through Milestone 2 |
| Access | L1 Designed | RBAC exists; ABAC and templates need maturity |
| Organizations | L0 Concept | Planned |
| Workspaces | L1 Designed | Architecture exists; implementation pending |
| People | L2 Implemented | Partial owner console support |
| Invitations | L3 Locally Verified | Product Owner workflow still requires production acceptance |
| Provisioning | L1 Designed | Future slices |
| Onboarding | L1 Designed | EPIC-001 defines the platform onboarding engine |
| Persona Engine | L1 Designed | EPIC-001 defines persona-driven configuration |
| Workflow | L0 Concept | Planned platform service |
| Documents | L0 Concept | Planned |
| Notifications | L1 Designed | Outbox pattern exists in milestone docs |
| Activation | L1 Designed | EPIC-001 defines activation and first business outcome |
| Dashboard | L1 Designed | Dynamic engine not yet implemented |
| Navigation | L1 Designed | Dynamic engine not yet implemented |
| Audit | L2 Implemented | Partial |
| Reporting | L0 Concept | Mock/partial UI exists |
| Billing | L0 Concept | Planned |
| AI | L0 Concept | Planned |

---

## Quality Gate

A capability may not be marked enterprise ready until:

- Business rules are complete.
- Service boundary is clear.
- Database ownership is clear.
- API contracts are defined.
- Permission model is complete.
- UX flows have no dead ends.
- Audit events are defined.
- Failure handling is defined.
- Runtime verification is possible through the application UI.
