# External Consultant P1 practice operations architecture

## Ownership audit

| Capability | Decision | Owner |
| --- | --- | --- |
| Authentication, tenant membership, RBAC | REUSE | Auth Service |
| Client profile and canonical client identity | REUSE | Profile/Fiteatsy services |
| Reports and biomarkers | REUSE | Existing report intelligence |
| Food catalogue and diet plans | REUSE | Nutrition/Fiteatsy services |
| Secure files and media | REUSE | Existing document storage |
| In-app notification inbox | EXTEND through events | Auth Service |
| Consultations, follow-ups, goals, tasks, check-ins, adherence, notes, calendar projection | NEW | Practice Operations Service |
| Transactional domain events | NEW | Practice Operations `service_outbox_events` |

Practice Operations is one bounded context, not one service per page. It uses the existing
canonical `tenant_id` and external `client_id`; it never creates an alternate client identity.
The gateway supplies authenticated actor, role, tenant and permission headers. Every query
contains a tenant predicate and client-scoped resources remain tenant constrained.

## Frozen boundary

The service is exposed only at `/api/v1/practice-operations`. Existing ZESTIVA_INTERNAL
routes, tables, diet lifecycle, reports, DOCX, assignment authority and navigation are not
modified. The frontend mounts P1 navigation only inside `ExternalSaaSWorkspace`.

## Event model

Mutations write the resource and an outbox event in the same database transaction. Consumers
may create in-app notifications or refresh projections. Publishing is retryable and does not
require synchronous cross-service database writes.

## Data safety

- UUID primary keys and deterministic cursor pagination.
- Tenant and canonical external client identifiers on client resources.
- Idempotency keys on repeatable creates.
- Integer `version` for optimistic concurrency.
- Structured errors with `code`, `safe_message`, `correlation_id`, and `retryable`.
- No PHI in notification payload previews or routine logs.
