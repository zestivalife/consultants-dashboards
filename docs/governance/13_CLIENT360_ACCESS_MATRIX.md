# Client 360 access matrix

This matrix is the canonical release contract for Consultant Client 360. An authenticated allowed role with an active, in-scope assignment has access to the assigned client workspace. `CONSULTANT_ACCESS_V1` is not a Consultant workspace business gate. Historical consent records may remain for compatibility and audit, but they must not authorize, deny, hide, or disable Client 360.

| Surface | Assigned Consultant | Assigned Senior Consultant | Unassigned or inactive |
| --- | --- | --- | --- |
| Roster | Client visible | Client visible according to governed role scope | Hidden |
| Header | Visible | Visible | Denied |
| Overview | Visible | Visible | Denied |
| Profile | Visible | Visible | Denied |
| Health Intelligence | Visible | Visible | Denied |
| Nutrition | Visible | Visible | Denied |
| Diet Plan | Visible; actions remain role/lifecycle constrained | Visible; review actions remain role/lifecycle constrained | Denied |
| Reports | Visible | Visible | Denied |
| Biomarkers | Visible | Visible | Denied |
| Activity / wearable data | Visible | Visible | Denied |
| Care | Visible | Visible | Denied |
| Timeline | Visible | Visible | Denied |

## Canonical authorization rule

```text
AUTHENTICATED + ROLE_ALLOWED + ACTIVE_ASSIGNMENT + DOMAIN_PERMISSION = ALLOW
```

- Assignment must be active, within its start/end window, and scoped to the FitEatsy Consultant relationship.
- Direct cross-client or cross-consultant access remains denied.
- Senior Consultant access follows the governed role and assignment rules; it is not a global bypass.
- `CONSULTANT_ACCESS_V1` has no place in this authorization decision.

## Request authority

- `GET /v1/consultants/clients` and every assigned-client context use the same active-assignment authority.
- `GET /v1/consultants/clients/:clientId/workspace` returns the full assigned-client workspace.
- Care operations use `/v1/consultants/clients/:clientId/operations` under the same assignment boundary.
- Domain routes must resolve authentication, allowed role, active assignment, and their own domain permission before returning data.

## Error semantics

- `401 AUTH_REQUIRED`: do not render Client 360.
- `403 CLIENT_ASSIGNMENT_REQUIRED`: deny the entire Client 360 surface.
- Network, timeout, and `5xx`: render an explicit retryable error; never render a false zero or empty-success state.
- `CONSULTANT_ACCESS_CONSENT_REQUIRED` is deprecated for Consultant workspace access and must not be emitted or interpreted as a workspace gate.

## Diet lifecycle

```text
Consultant draft
→ Consultant submits exact version
→ Senior Consultant requests changes or approves that exact version
→ Consultant revises/resubmits when required
→ Consultant explicitly publishes an approved exact version
→ Client receives only the published version
```

Approval does not publish. A newer draft does not replace the currently published version. Only the exact approved version is publishable.

## Historical consent data

The existing consent schema, events, and legacy transport may remain for data compatibility and audit history. They are not workspace authority and must not be used to filter the roster, block a Client 360 section, or suppress assigned-client fields.

## Freeze rule

Any change to roster visibility, Client 360 routes, assignment resolution, role/domain permission, error mapping, or diet lifecycle must preserve this matrix and update its regression contract deliberately.
