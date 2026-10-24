# External Nutrition API Contract Matrix

Status values: `S` source present, `T` automated test evidence, `L` live authenticated evidence.

| Domain | Method and endpoint | Owner | Consumer | Auth / isolation | Validation / response | Status and gap |
|---|---|---|---|---|---|---|
| Clients | `GET/POST /v1/external/clients` | Fiteatsy | `fiteatsyConsultantsApi.js` | bearer; assigned External tenant expected | filters / client projection | S,T; L absent; canonical phone dedupe not proven |
| Client360 | `GET /v1/external/clients/{id}/360` | Fiteatsy | External Client360 | bearer, client scope | composite payload | S,T; multiple downstream owners inside projection |
| Profile | `PATCH /v1/external/clients/{id}/profile` | Fiteatsy | Client360 editors | bearer, client scope | section + values | S,T; provenance/version contract incomplete |
| Enrichment | `GET/PUT /api/v1/practice-operations/clients/{id}/profile-enrichment` | Practice Operations | profile enhancements | JWT + tenant resolver | optimistic version, allowlisted fields | S,T; merge with base source occurs in frontend |
| Intake invite | `POST /v1/external/clients/{id}/invitations` and current/revoke/regenerate | Fiteatsy | Client360 | bearer, client scope | scoped token | S,T; delivery/provider evidence absent |
| Profession intake | `POST /api/v1/practice-operations/clients/{id}/profession-intake-invitations` | Practice Operations | External workspace | JWT + tenant | expiry, template, audit | S,T; duplicates Fiteatsy intake purpose |
| Public intake | `GET/PATCH/POST /v1/external/intake/{token}/*` | Fiteatsy | client intake | signed token | section, consent, submit | S,T; production replay evidence absent |
| Practice intake | `GET/PATCH/POST /api/v1/profession-intake/{token}/*` | Practice Operations | profession forms | hashed signed token, tenant/client bound | required answers, completion | S,T; second token system/purpose overlap |
| Documents | `GET/POST/PATCH/DELETE /v1/external/clients/{id}/documents*` | Fiteatsy | Health Records/Reports | bearer, client scope | multipart metadata | S,T; PDF signature enforcement not evidenced in this repo |
| Extraction | `POST .../documents/{doc}/process`, `GET .../extraction` | Fiteatsy | report review | bearer, client/doc scope | extraction state | S,T; exact source retention linkage not proven |
| Biomarkers | `GET /v1/external/clients/{id}/biomarkers` | Fiteatsy | Biomarkers tab | bearer, client scope | observation projection | S,T; plan consumer missing |
| Biomarker history | `GET .../biomarkers/{biomarker}/history` | Fiteatsy | history UI | bearer, client scope | dated provenance rows | S,T |
| Review | `POST/PATCH .../biomarker-observations/{id}` | Fiteatsy | review UI | bearer, client scope | confirm/correct/reject | S,T; live audit not verified |
| Multi plans | `GET/POST /v1/external/clients/{id}/diet-plans` | Fiteatsy | Multi Diet Plan | bearer, client scope | targets + plan identity | S,T; assessment reference absent |
| Plan draft | `PUT .../diet-plans/{plan}/draft` | Fiteatsy | editor | bearer, client + plan scope | options snapshot | S,T |
| Plan publish | `POST .../diet-plans/{plan}/publish` | Fiteatsy | editor | bearer, capability | lifecycle validation | S,T; clinical readiness binding unproven |
| Plan history | `GET .../history`, versions, compare, duplicate, download | Fiteatsy | history/DOCX UI | bearer, client scope | immutable version projection expected | S,T |
| Common Food | `/v1/external/clients/{id}/diet-plans/{plan}/common-food/*` | Fiteatsy | unified editor | bearer, plan/client scope | server nutrient totals, version checks | S,T; Fiteatsy is frozen external dependency |
| Practice plans | `/api/v1/practice-operations/diet-plans*` | Practice Operations | `practiceOperationsApi.js` | JWT + tenant + profession capability | lifecycle + totals | S,T; duplicate plan aggregate |
| Nutrition intelligence | `GET /v1/consultants/clients/{id}/nutrition-intelligence` | Fiteatsy | `PlatformWorkspace.jsx` | bearer | scores/focus/observations | S,T; not the External Client360 canonical assessment |
| Progress | `GET/POST /api/v1/practice-operations/clients/{id}/progress*` | Practice Operations | Progress UI | JWT + tenant | definitions/observations/targets/milestones | S,T; no assessment/plan version FK |
| Document vault | `/api/v1/practice-operations/documents*` | Practice Operations | Documents workspace | JWT + tenant + visibility | object reference/version/checksum | S,T; no canonical lab-report cross-reference |
| Calendar sync | `/api/v1/practice-operations/calendar-sync*` | Practice Operations | Calendar workspace | JWT + tenant | provider connection/busy/external change | S,T; runtime OAuth not configured/verified |
| Legacy report | `POST /api/v1/profile/upload-report` | Profile Service | no confirmed active External consumer | JWT | simulated extracted values | S only; unsafe for clinical use |
| Legacy nutrition | `/api/v1/nutrition/diet-plan`, templates, assign, upload-report | Nutrition Service | no confirmed active External consumer | JWT | generic plan/report records | S only; disconnected duplicate |

## Contract decisions for Phase 2

1. Keep active Fiteatsy contracts read-only from an ownership perspective; do not modify Fiteatsy under this program.
2. Introduce an External-owned orchestration/read model in Practice Operations only if it can reference Fiteatsy IDs without copying clinical truth.
3. A new assessment contract must include `assessment_id`, `version`, `client_id`, `tenant_id`, input references, calculation methodology versions, reviewer, readiness, and staleness.
4. Plan create/publish must accept or resolve that assessment reference and fail closed on cross-client/cross-tenant mismatch.
5. Never route External clinical traffic to the legacy random report processor.

