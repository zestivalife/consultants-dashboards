# Release freeze manifest

Status: `PENDING_FINAL_ACCEPTANCE`

This manifest becomes `ACTIVE` only after local validation, exact-SHA CI, deployment, runtime-SHA parity, and authenticated production acceptance all pass. Its presence does not itself authorize deployment or seal an unverified candidate.

## Protected contracts

1. `CONSULTANT_ASSIGNMENT_ACCESS` — authenticated allowed role + active assignment + domain permission is the access authority.
2. `CONSULTANT_ROSTER` — every visible client satisfies the same canonical assignment model used by Client 360.
3. `CLIENT360_FULL_ASSIGNED_ACCESS` — all assigned-client tabs are available without `CONSULTANT_ACCESS_V1`.
4. `CROSS_CLIENT_ISOLATION` — unassigned, inactive, ended, revoked, or cross-consultant access is denied.
5. `FALSE_ZERO_HANDLING` — failures render explicit errors, never a fabricated zero-client success state.
6. `DIET_DRAFT_LIFECYCLE` — draft and revision work never alter the published client version.
7. `SENIOR_REVIEW` — Senior Consultant review produces a change request or exact-version approval.
8. `EXACT_VERSION_APPROVAL` — approval applies only to the reviewed immutable version.
9. `CONSULTANT_EXPLICIT_PUBLISH` — approval never auto-publishes; publication is a separate explicit action.
10. `CLIENT_PUBLISHED_VERSION` — clients receive only the exact explicitly published version.
11. `RUNTIME_PARITY` — production acceptance requires deployed frontend/backend identities to match accepted SHAs.

## Activation gates

- Focused authorization and diet-lifecycle tests pass.
- Full relevant regressions pass twice.
- Backend and frontend builds pass.
- Exact-SHA governed CI passes.
- Backend and frontend deployments report exact runtime parity.
- Authenticated production roster, Client 360 tabs, isolation, false-zero behavior, and diet lifecycle pass.

Until every gate passes, engineering seal status remains `NOT_ACTIVE`.
