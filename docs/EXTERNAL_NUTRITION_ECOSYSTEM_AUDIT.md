# External Nutrition Ecosystem Audit

Date: 2026-10-24  
Mode: Phase 1, read-only  
Scope: Zestiva External Consultant only

## Executive conclusion

The External Consultant nutrition journey is substantial but is not one coherent bounded system. The production Client360 primarily consumes Fiteatsy `/v1/external/*` APIs through the same-origin `/api/fiteatsy` proxy (`nuetra-frontend/lib/fiteatsyConsultantsApi.js`), while Practice Operations owns a second diet-plan lifecycle (`services/practice-operations-service/app/main.py:1155-1277`) and the legacy nutrition/profile services own additional disconnected diet, report, biomarker, and measurement models. This is the dominant data-lineage and ownership risk.

The current frontend and Practice Operations source regressions pass (472/472 and 271/271 respectively). Those results establish source-level behavior only. No authenticated production client record was mutated or used during this audit, so all authenticated live workflow cells remain `LIVE_BROWSER_NOT_VERIFIED`.

## Baseline

| Service | Repository/source SHA | Runtime SHA | Deployment | Health | Migration | Parity | Evidence |
|---|---|---|---|---|---|---|---|
| Consultant frontend | `37fa06077165e795dcc056e443c4c58da041aa1d` | same | `dpl_DcmCsJxt6MGX94sUCikv66D6tRp8` | version endpoint responsive | n/a | PASS | `GET https://consultant.nuetra.in/api/version` |
| API Gateway | source inspected at frontend worktree; runtime differs | `ac6410e8812bf5a8ca78ea87bc9e6b4f3cbd7dbf` | `73d1049a-51f5-4edf-8fca-d245f547801e` | healthy | unknown | RUNTIME IDENTIFIED | `/api/v1/versions` |
| Practice Operations | historical and runtime | `a9c9a4e8395b6ec8336bb25eca4f4236ec89c243` | not exposed by version response | responsive through aggregator | runtime endpoint omits head | PARTIAL | `/api/v1/versions` |
| Auth Service | frozen | `e602a7be59f592529c2adfd7a4ea9d567b181fa3` | `6b7a5915-68ec-457b-92b3-1bd6f9ebe9cc` | responsive | `b6c7d8e9f0a1` | OBSERVED, NOT AUDITED | `/api/v1/versions` |
| Profile Service | legacy/disconnected candidate | unknown | `30c98900-f36d-422e-817c-87846bb82a1c` | responsive | unknown | UNVERIFIABLE | `/api/v1/versions` |
| Assessment/Nutrition/Scoring | legacy/disconnected candidates | not reported | Railway reports online; latest deploy failed | liveness response only | unknown | UNVERIFIABLE | Railway inventory and `/api/v1/versions` |

Origin `main` is `fb6e40dd11569c67b68a0c9f6ee5bff4af9ca7cc`; the audited release branch and origin are both `37fa060…`. The worktree was clean before documentation was added.

## Actual architecture

1. `nuetra-frontend/components/external/ExternalConsultantWorkspace.jsx` mounts the External shell and profession configuration.
2. `ExternalClient360.jsx` and `ProfessionClient360.jsx` compose capability-gated Client360 modules.
3. `fiteatsyConsultantsApi.js` directly owns the active External client, document, report extraction, biomarker, diet-plan, common-food, intake, and Client360 contracts.
4. Browser production requests use `/api/fiteatsy`; the frontend proxy routes them to the existing Fiteatsy service. This audit does not authorise changing that service.
5. `practiceOperationsApi.js` separately owns consultation, follow-up, goals, tasks, profession intake, documents, progress, portal, calendar-sync, and a second diet-plan contract.
6. Gateway validates JWT and resolves External tenant context for Practice Operations (`api-gateway/app/routers/practice_tenant_resolver.py`).

## Screen audit

| Surface | Source | Status | Evidence / gap |
|---|---|---|---|
| Clients | `ExternalConsultantWorkspace.jsx`, `fiteatsyConsultantsApi.js:116-159` | SOURCE_PRESENT, TESTED | Pagination and false-zero tests pass; E.164/provider normalization not proven end-to-end live. |
| Overview | `ExternalClient360.jsx`, `ProfessionClient360.jsx` | SOURCE_PRESENT, TESTED | Explicit loading/error/empty states; missing-field contradiction can occur because base Fiteatsy fields and Practice Operations enrichment/completion are composed from different owners. |
| Health Profile | `ExternalClientHealthIntake.jsx`, `ExternalClientProfileEnhancements.jsx` | PARTIAL | Client intake and consultant enrichment exist, but a single versioned provenance projection is absent. |
| Biomarkers | `ExternalBiomarkerReview.jsx`, `ExternalBiomarkerHistory.jsx` | SOURCE_PRESENT, TESTED | Confirmation/history/provenance present; consumption by a versioned nutrition assessment is not proven. |
| Health Records | `ExternalHealthRecords.jsx` | PARTIAL | Metadata and linkage UI exist. Source-object retention and historical record reconciliation are not one authoritative contract. |
| Measurements | `ExternalClientProfileEnhancements.jsx`, `externalClientProfile.mjs` | PARTIAL | Persistence fields exist; BMI and WHR are recomputed in frontend, duplicating backend/scoring responsibility. |
| Reports | `ExternalTransientReportAnalyzer.jsx`, document APIs | BROKEN LINEAGE RISK | Biomarkers may survive when the source document is absent/unlinked; legacy profile upload generates simulated random biomarkers (`profile_service.py:288-326`). |
| Nutrition & Care | `ProfessionClient360.jsx`, `ExternalMultiDietPlan.jsx` | PARTIAL | Authoring is broad and tested, but multiple API owners and no immutable assessment snapshot leave provenance/staleness unresolved. |
| Progress | Practice Operations progress routes and Client360 tabs | SOURCE_PRESENT | Generic observations/targets exist; nutrition adherence and assessment-version linkage are incomplete. |
| Documents/Admin | Practice Operations vault plus Fiteatsy documents | DUPLICATE OWNERSHIP | Two document domains exist without a canonical cross-reference contract. |
| Calendar | `ExternalCalendarWorkspace.jsx`, migration `0042_calendar_sync.py` | PROVIDER NOT CONFIGURED / PARTIAL | Schema permits Google and Microsoft; target says Google only. OAuth/token runtime readiness not verified. |

## Findings

### P0

| ID | Finding | Root cause and evidence | Required outcome |
|---|---|---|---|
| NUT-P0-01 | No authoritative nutrition assessment snapshot binds a published plan to exact inputs. | Fiteatsy plan calls accept targets/options; Practice Operations snapshots totals but not full clinical input provenance (`main.py:1179,1210`). | External-owned immutable assessment/version reference on every plan version. |
| NUT-P0-02 | Biomarker-to-plan consumption is not traceable. | Biomarkers are fetched/displayed independently from diet-plan APIs in `fiteatsyConsultantsApi.js`; no assessment identifier appears in the plan contract. | Confirmed-only biomarker projection with source IDs, methodology version, review state, and consumer tests. |
| NUT-P0-03 | Legacy profile report processing fabricates clinical values. | `services/profile-service/app/services/profile_service.py:288-326` uses random values while claiming report processing. | Keep disconnected from External production; retire route or replace only in an isolated future release with canonical ingestion. |
| NUT-P0-04 | Clinical/document ownership is split across Fiteatsy documents, Practice Operations vault, and legacy health reports. | `fiteatsyConsultantsApi.js:190-242`; migrations `0023_document_vault.py`; nutrition `health_reports`. | Declare canonical source-document owner and use immutable cross-service references. |
| NUT-P0-05 | Calculation ownership is duplicated. | BMI/WHR in `externalClientProfile.mjs:20-30`; BMI scoring in scoring service; plan targets are accepted rather than derived in nutrition/Practice Operations. | One versioned External calculation owner; frontend renders results only. |

### P1

- NUT-P1-01: reconcile base identity and enrichment completion to eliminate false missing-field warnings.
- NUT-P1-02: PDF-only lab upload with MIME and file-signature verification through the canonical ingestion route.
- NUT-P1-03: connect source document, extraction run, confirmation, Health Record, and observation IDs.
- NUT-P1-04: normalize phone to E.164 at persistence and digits-only only at provider boundary.
- NUT-P1-05: implement assessment staleness triggers for measurements, confirmed biomarkers, intake, medications, allergies, and goals.
- NUT-P1-06: reduce calendar provider scope to Google without deleting historical Microsoft rows.

### P2

- NUT-P2-01: longitudinal nutrient-target coverage and adherence analytics.
- NUT-P2-02: richer explainability UI for why an assessment input affected a plan.
- NUT-P2-03: consolidated operational observability for ingestion and plan lifecycle.

## Working capabilities

- Capability-gated nutrition/biomarker/Diet Plan tabs.
- External client listing with failure-versus-empty protection.
- Client intake token flow, review surfaces, and audit tables.
- Report metadata upload/process/review UI and biomarker confirmation/history UI.
- Multi-plan draft/save/publish/history/DOCX contracts.
- Governed seven-meal-head Common Food authoring with server-owned nutrient totals.
- Tenant resolver and client-specific route guards.
- Practice Operations documents, progress, portal, WhatsApp preparation, and calendar foundations.

## Verification classification

- Source inspection: PASS for the paths cited above.
- Frontend automated tests: 472/472 PASS.
- Practice Operations automated tests: 271/271 PASS.
- Production public version/health: PASS.
- Authenticated live API and browser: NOT VERIFIED in this audit.
- Production database records/schema head: NOT QUERIED; no patient data access or mutation performed.

## Freeze proof

Internal authentication, Internal Super Admin flows/accounts, Internal role behavior, Fiteatsy source/data, `api.nuetra.in`, production credentials, deployments, and clinical records were not modified. Documentation-only changes are confined to `docs/EXTERNAL_*`.

