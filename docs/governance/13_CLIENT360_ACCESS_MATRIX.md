# Client 360 access matrix

This matrix is the release contract for the Consultant Client 360 surface. Assignment establishes the client shell and operational relationship. Consultant-access consent separately governs health, clinical, nutrition, report, biomarker, wearable, and other sensitive content.

| Surface | Assigned, no consent | Assigned, valid consent | Unassigned |
| --- | --- | --- | --- |
| Header | Name, programme, assignment state; protected-data status only | Full authorised header | Denied |
| Overview | Assignment-safe client identity and assignment state | Full authorised overview | Denied |
| Profile | Name, programme, assignment state; protected profile fields hidden | Full authorised profile | Denied |
| Health | Section-level consent gate | Full authorised health data | Denied |
| Nutrition | Section-level consent gate | Full authorised nutrition data | Denied |
| Diet Plan | Workflow shell only; nutrition and plan content/actions hidden | Full authorised plan workflow | Denied |
| Reports | Section-level consent gate | Full authorised reports | Denied |
| Care | Consultations, tasks, follow-ups, goals; clinical notes hidden | All authorised care operations | Denied |
| Timeline | Assignment event only; protected events hidden | Full authorised timeline | Denied |

## Field-level contract

The table below is authoritative for the fields and controls currently rendered by Client 360. `Visible` means the value may be rendered for an active assignment. `Gated` means the value and its action must not be rendered until consultant-access consent is valid. `Denied` means the Client 360 shell itself must not render.

| Location | Field, card, or action | Assigned, no consent | Assigned, valid consent | Unassigned |
| --- | --- | --- | --- | --- |
| Header | Client name | Visible | Visible | Denied |
| Header | Programme label | Visible | Visible | Denied |
| Header | Assignment state | Visible | Visible | Denied |
| Header | Consent/protected-data state | Visible | Visible | Denied |
| Header | Phone/contact identity | Gated | Visible | Denied |
| Header | Health status | Gated | Visible | Denied |
| Header | Profile completion | Gated | Visible | Denied |
| Header | Health-sync state and timestamp | Gated | Visible | Denied |
| Header | Published/editable diet-plan versions | Gated | Visible | Denied |
| Overview | Client identity and active assignment | Visible | Visible | Denied |
| Overview | Health snapshot and health-status card | Gated | Visible | Denied |
| Overview | Risk flags and recommended actions | Gated | Visible | Denied |
| Overview | Wellness Intelligence and source metadata | Gated | Visible | Denied |
| Overview | Nutrition Intelligence | Gated | Visible | Denied |
| Overview | Biomarker snapshot | Gated | Visible | Denied |
| Profile | Client name, programme, assignment state | Visible | Visible | Denied |
| Profile | Age, gender, height, weight | Gated | Visible | Denied |
| Profile | BMI, body fat, waist, hip, neck, goal weight | Gated | Visible | Denied |
| Profile | Medical conditions and history | Gated | Visible | Denied |
| Profile | Sleep, stress, activity, food preferences, allergies and dislikes | Gated | Visible | Denied |
| Health | Biomarker values, ranges, dates, sources and history | Gated | Visible | Denied |
| Health | Activity and wearable summaries | Gated | Visible | Denied |
| Nutrition | Energy, protein, hydration and adherence targets | Gated | Visible | Denied |
| Diet Plan | Assigned-client workflow identity and access state | Visible | Visible | Denied |
| Diet Plan | Targets, restrictions, meal candidates/selections and plan content | Gated | Visible | Denied |
| Diet Plan | Version lifecycle, generation, review, publish and export actions | Gated | Visible subject to role | Denied |
| Reports | Report dates, filenames/titles, processing state and extracted biomarkers | Gated | Visible | Denied |
| Care | Consultations | Visible | Visible | Denied |
| Care | Tasks | Visible | Visible | Denied |
| Care | Follow-ups | Visible | Visible | Denied |
| Care | Goals | Visible | Visible | Denied |
| Care | Clinical notes | Gated | Visible | Denied |
| Care | Create/update assignment-safe operations | Visible | Visible | Denied |
| Care | Create/update clinical notes | Gated | Visible | Denied |
| Timeline | Active-assignment event | Visible | Visible | Denied |
| Timeline | Health, clinical, report, nutrition and wearable events | Gated | Visible | Denied |

The current UI has no separate assignment-safe header fields for client identifier, avatar, contact-status indicator, consultation indicator, or task indicator. Adding any of them requires an explicit product/privacy decision and a corresponding matrix and regression update.

## Request authority

- `GET /v1/consultants/clients/:clientId/workspace` is the shell/protected-data boundary.
- Only the exact `403 CONSULTANT_ACCESS_CONSENT_REQUIRED` response is converted into the section-level protected-access state.
- Authentication, role, assignment, cross-consultant, inactive-assignment, not-found, network, timeout, and server failures are rethrown and remain global fail-closed errors.
- Care operations use `/v1/consultants/clients/:clientId/operations`; the UI excludes `NOTE` records and the note creation option while protected access is denied. Backend assignment and authorization enforcement remains mandatory.

## Error semantics

- `401 AUTH_REQUIRED`: the Client 360 surface is not rendered.
- Assignment denial (`403 CLIENT_ASSIGNMENT_REQUIRED`, inactive assignment, or cross-consultant access): the entire Client 360 surface is denied.
- `403 CONSULTANT_ACCESS_CONSENT_REQUIRED`: the assigned-client shell remains visible and only protected sections are gated.
- Network, timeout, and `5xx` failures: render an explicit error state; never render a false zero, empty-success state, or consent state.

## Protected fields

Without valid consultant-access consent, the UI must not render phone/contact details, health status, profile completion, health-sync metadata, body measurements, medical history, medication details, lifestyle data, biomarkers, wearable metrics, nutrition targets, plan content or versions, reports, clinical notes, or protected timeline events.

## Freeze rule

Any change to the roster, Client 360 tabs, workspace request, operations UI, or authorization error mapping must retain the three-persona matrix above and update the regression contract when behavior intentionally changes.
