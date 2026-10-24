# External Nutrition Implementation Blueprint

This is an implementation-ready Phase 2 proposal. It authorises nothing by itself.

## Architecture decision

Use Practice Operations as the External orchestration and audit owner while preserving existing authoritative systems through IDs and read contracts. Do not modify Internal authentication/roles, Internal Client360, Fiteatsy source/data, or `api.nuetra.in`. Where Fiteatsy lacks a needed write contract, add an External-owned crosswalk/snapshot rather than patching the frozen service.

## Proposed additive External schema

1. `external_nutrition_assessments`
   - tenant/client/profession, status/readiness, current version, reviewer, stale state/reason.
2. `external_nutrition_assessment_versions`
   - immutable methodology versions, input manifest/checksums, results, limitations, created/reviewed timestamps.
3. `external_nutrition_assessment_inputs`
   - source system/type/id/version, effective date, confirmation status, unit/provenance reference.
4. `external_diet_plan_assessment_links`
   - tenant/client, external plan ID/version, assessment/version; unique and immutable after publication.
5. `external_nutrition_staleness_events`
   - triggering source/version, previous assessment version, resolution.
6. `external_clinical_document_links`
   - source document, health record, extraction run and observation reference crosswalk; no copied PDF bytes.

All migrations must be additive, tenant-keyed, indexed on `(tenant_id, client_id)`, use restrictive foreign-key behavior where local references exist, and have a tested downgrade that refuses destructive rollback after production data is written unless explicitly approved.

## Proposed APIs

- `GET /api/v1/practice-operations/clients/{client}/nutrition-assessment`
- `POST /api/v1/practice-operations/clients/{client}/nutrition-assessments`
- `POST /api/v1/practice-operations/nutrition-assessments/{id}/review`
- `GET /api/v1/practice-operations/nutrition-assessments/{id}/versions/{version}`
- `GET /api/v1/practice-operations/clients/{client}/nutrition-readiness`
- `POST /api/v1/practice-operations/clients/{client}/clinical-document-links/reconcile` (administrative, idempotent, read-verified)
- `GET /api/v1/practice-operations/clients/{client}/nutrition-lineage`

Each route requires verified JWT, active External tenant membership, client assignment, capability enforcement, idempotency for writes, correlation ID, and audit event. No route may share Internal prefixes or alter Internal middleware behavior.

## Ordered phases

1. **P0 ownership lock:** formally choose canonical owners; block External access to legacy simulated report processing; add contract tests.
2. **P0 assessment foundation:** additive schema/API, confirmed-only evidence manifest, versioned calculations, capability and tenant gates.
3. **P0 plan binding:** adapter/crosswalk binds existing Fiteatsy plan versions to assessment versions without modifying Fiteatsy.
4. **P1 document lineage:** reconcile source document → extraction → Health Record → observation references; never fabricate missing files.
5. **P1 Client360 projection:** one External read model for completion, nutrition readiness, calculations, and evidence.
6. **P1 intake/WhatsApp:** consolidate user-visible request flow, E.164 identity, secure scoped links and audit.
7. **P1 Google Calendar:** Google-only new connections, encrypted secret references, refresh/error behavior; preserve historical Microsoft data.
8. **P2 monitoring:** plan-bound adherence, progress, reassessment triggers, explainability and analytics.

## Exact source areas

- Frontend: `nuetra-frontend/components/external/*`, `lib/fiteatsyConsultantsApi.js`, `lib/practiceOperationsApi.js`, `lib/externalClientProfile.mjs`.
- Gateway: only External Practice Operations proxy/tenant enforcement tests; no Internal auth middleware change.
- Practice Operations: new isolated modules/routers rather than expanding `main.py`; new migrations after `0053` with verified chain.
- Tests: frontend contract/state tests, Practice Operations API/domain tests, gateway tenant/capability tests, isolated integration DB, browser QA.

## Safety gates

- Confirmed observations only; qualitative values explicitly supported.
- Never diagnose or auto-prescribe from abnormal flags.
- Draft may be allowed with explicit missing-data state; publish is server-blocked for critical readiness failures.
- Published plan and assessment versions immutable.
- Cross-client/cross-tenant references denied and audited.
- PDF-only lab ingestion with MIME and magic-byte validation.
- No source-report bytes in the new orchestration tables.

## Acceptance matrix

Each cell must distinguish source present, automated pass, integration pass, live API verified, and live browser verified. Minimum end-to-end scenarios:

- E.164 client create/deduplicate/WhatsApp request.
- Client-owned intake save/reload/submit/version/provenance.
- PDF upload/storage/extraction/review/confirmation/Health Record/biomarker trend.
- Measurements → versioned BMI/WHR/approved energy methodology.
- Confirmed biomarkers + intake + measurements → reviewed assessment snapshot.
- Assessment-bound seven-head/five-option draft → reload → publish → portal → DOCX.
- Changed input marks assessment/plan stale without rewriting history.
- Profession denial, client denial and tenant denial.
- Google connect/sync/reschedule/cancel/timezone/reauth.
- 360/390/414 responsive verification.

## Deployment and rollback

1. Isolated production-compatible DB migration test and restore test.
2. Exact-SHA CI for affected External frontend, Gateway (only if routing changes), and Practice Operations.
3. Fresh backup/recovery point.
4. Apply additive migration before backward-compatible service deployment.
5. Deploy Practice Operations, then affected Gateway, then frontend.
6. Verify runtime SHAs, migration head, health/readiness, live authenticated matrix.
7. Roll back application binaries first; additive tables remain dormant. Do not drop populated clinical/audit tables during incident rollback.

## Frozen-domain impact rule

If any phase requires changing Internal authentication, Internal Super Admin accounts/roles, Internal Client360, Fiteatsy source/data, or `api.nuetra.in`, stop and return `FREEZE_IMPACT`. The default solution is an External-only adapter, crosswalk, or read model.

