# Release freeze manifest

Status: `ACTIVE`

Engineering seal: `ACTIVE`

In-house product line: `ZESTIVA / NUETRA / FITEATSY`

Development state: `FROZEN`

Seal document: [Consultant Diet Plan Engineering Seal](./CONSULTANT_DIET_PLAN_ENGINEERING_SEAL.md)

## Accepted production implementation

- Backend SHA: `0fc45e318216b19487f580c34d14092aef3b71b0`
- Frontend SHA: `587179495c63ed23504bcb637964350ef7327efa`
- Production acceptance: `PASS`
- Exact-SHA CI: `PASS`
- Backend runtime parity: `PASS`
- Frontend runtime parity: `PASS`

Governance commits created after acceptance document the freeze only. They do not replace or change the accepted production implementation SHAs above.

## Final in-house recovery acceptance

- Backend repair SHA: `e868f9cf413c051c913682336b7b3d42d0b252cb`
- API Gateway repair SHA: `4eb7829be5e32d7a200cc846fe72faf15ad682b7`
- Profile Service runtime repair SHA: `bb6ed2277c89174e00c7e0f8cef6d4ae255b2fcb`
- Governed QA classification: `GOVERNED_QA_INHOUSE`
- Client Profile Me: `PASS`
- Client exact published-plan read: `PASS`
- Practitioner workspace and denied authority boundaries: `PASS`
- Client role isolation: `PASS`
- Persona logout and stale-context clearing: `PASS`
- Platform Authority Matrix: `PASS`
- Cross-client leakage: `0`
- Cross-tenant leakage: `0`
- Role escalation: `NONE`

## Frozen protected features

| Feature ID | Status | Permanent regression ownership |
| --- | --- | --- |
| `CONSULTANT_ASSIGNMENT_ACCESS` | `FROZEN_PROTECTED` | [`client360-contract.test.mjs`](../../nuetra-frontend/tests/client360-contract.test.mjs) |
| `CONSULTANT_ROSTER` | `FROZEN_PROTECTED` | [`client-roster-failure-contract.test.mjs`](../../nuetra-frontend/tests/client-roster-failure-contract.test.mjs), [`client360-contract.test.mjs`](../../nuetra-frontend/tests/client360-contract.test.mjs) |
| `CLIENT360_ASSIGNED_ACCESS` | `FROZEN_PROTECTED` | [`client360-contract.test.mjs`](../../nuetra-frontend/tests/client360-contract.test.mjs) |
| `CROSS_CLIENT_ISOLATION` | `FROZEN_PROTECTED` | [`client360-contract.test.mjs`](../../nuetra-frontend/tests/client360-contract.test.mjs), backend authorization suites |
| `FALSE_ZERO_HANDLING` | `FROZEN_PROTECTED` | [`client-roster-failure-contract.test.mjs`](../../nuetra-frontend/tests/client-roster-failure-contract.test.mjs) |
| `DIET_PLAN_DRAFT` | `FROZEN_PROTECTED` | [`diet-builder-ux-repair.test.mjs`](../../nuetra-frontend/tests/diet-builder-ux-repair.test.mjs), backend lifecycle suites |
| `DIET_PLAN_SAVE_RELOAD` | `FROZEN_PROTECTED` | [`diet-builder-ux-repair.test.mjs`](../../nuetra-frontend/tests/diet-builder-ux-repair.test.mjs), backend lifecycle suites |
| `DIET_PLAN_SUBMIT` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs), backend lifecycle suites |
| `SENIOR_REVIEW_QUEUE` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs) |
| `SENIOR_REVIEW_AUTHORITY` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs) |
| `CHANGE_REQUEST_LIFECYCLE` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs), backend lifecycle suites |
| `DIET_PLAN_REVISION` | `FROZEN_PROTECTED` | [`diet-builder-ux-repair.test.mjs`](../../nuetra-frontend/tests/diet-builder-ux-repair.test.mjs), backend lifecycle suites |
| `DIET_PLAN_RESUBMISSION` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs), backend lifecycle suites |
| `EXACT_VERSION_APPROVAL` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs), backend approval suites |
| `APPROVAL_NOT_PUBLICATION` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs), backend approval suites |
| `CONSULTANT_EXPLICIT_PUBLISH` | `FROZEN_PROTECTED` | [`senior-diet-plan-review.test.mjs`](../../nuetra-frontend/tests/senior-diet-plan-review.test.mjs), backend publication suites |
| `CLIENT_PUBLISHED_VERSION` | `FROZEN_PROTECTED` | [`client360-contract.test.mjs`](../../nuetra-frontend/tests/client360-contract.test.mjs), backend publication suites |
| `CLIENT_PROFILE_ME` | `FROZEN_PROTECTED` | Authenticated production gateway/Profile Service acceptance |
| `PRACTITIONER_WORKSPACE` | `FROZEN_PROTECTED` | Governed role-matrix production acceptance |
| `PLATFORM_AUTHORITY_MATRIX` | `FROZEN_PROTECTED` | Governed role-matrix production acceptance |
| `CROSS_TENANT_ISOLATION` | `FROZEN_PROTECTED` | Backend tenant suites and governed production acceptance |
| `ROLE_ESCALATION_DENIED` | `FROZEN_PROTECTED` | Governed role-matrix production acceptance |
| `PERSONA_CONTEXT_CLEARING` | `FROZEN_PROTECTED` | Governed logout and persona-switch production acceptance |
| `BACKEND_RUNTIME_SHA_PARITY` | `FROZEN_PROTECTED` | Exact-SHA CI and production `/v1/version` acceptance evidence |
| `FRONTEND_RUNTIME_SHA_PARITY` | `FROZEN_PROTECTED` | [`runtime-build-identity.test.mjs`](../../nuetra-frontend/tests/runtime-build-identity.test.mjs) |

## Change control

Any change to a frozen feature requires all twelve steps in the [engineering seal](./CONSULTANT_DIET_PLAN_ENGINEERING_SEAL.md#mandatory-future-change-policy). No test, fixture, migration, historical implementation, or deployment may silently redefine this flow.
