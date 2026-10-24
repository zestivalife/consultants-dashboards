# External Nutrition Data Lineage

## Current lineage

### Client identity and intake

`External Clients UI` → `fiteatsyConsultantsApi.list/createExternalClient` → Fiteatsy client core → `/360` projection → External Client360.

Additional External-only enrichment follows:

`Client360 editor` → `practiceOperationsApi` → `external_client_profile_enrichments` (migration `0053_external_client_profile_enrichments.py`) → frontend merge in `externalClientProfile.mjs`.

Risk: completion/missing-field state is derived across base and enrichment sources rather than returned as one versioned authoritative projection.

### Report to biomarker

`PDF/document UI` → Fiteatsy `/documents` → `/process` → `/extraction` → consultant confirm/correct/reject → `/biomarkers` and history → Biomarkers/Health Records UI.

Known gap: source object, Health Record metadata, extraction run, and confirmed observation linkage cannot be proven from this repository as one immutable chain. Practice Operations document vault is separate. The legacy Profile Service upload path must not be used because it simulates biomarkers with random values.

### Measurements and calculations

Base measurements arrive from Fiteatsy Client360; External enrichment can add height, weight, waist, hip, neck and related values. `externalClientProfile.mjs` selects current values, calculates BMI and WHR, and feeds a diet-context projection.

Risk: calculated clinical values are owned by the presentation composition. Scoring service independently calculates BMI-derived scores. Neither proves a single methodology/version used by Diet Plan.

### Assessment to plan

Current path is implicit:

`Client360 context` → consultant-entered calorie/protein targets or Fiteatsy nutrition intelligence → plan/create or generate → Common Food candidate/options APIs → draft → publish → history/DOCX/portal.

Missing edge: there is no explicit immutable `nutrition_assessment_version_id` visible in the plan APIs. A later measurement or biomarker change therefore cannot reliably mark a plan stale without comparing unversioned projections.

### Monitoring

Practice Operations owns generic progress definitions, observations, targets, milestones, reports, engagement, follow-ups and portal views. Fiteatsy owns Diet Plan truth. No proven key binds adherence/progress observations to a precise published plan version and assessment snapshot.

## Target External-only lineage

1. Preserve client truth in its current authoritative source.
2. Create an External Practice Operations `external_nutrition_assessments` aggregate containing references, not copied clinical blobs where avoidable.
3. Store immutable assessment versions with source entity ID, source version/checksum, observed/effective date, confirmation status, and provenance.
4. Bind each External diet-plan version to exactly one assessment version through an additive reference/crosswalk owned outside Fiteatsy if the upstream contract cannot change.
5. Emit staleness events when a referenced input changes; never rewrite published plan history.
6. Bind monitoring observations to client, tenant, assessment version, plan/version, and source.

## Ten audited flows

| Flow | Current boundary | Status | First gap |
|---|---|---|---|
| Client → phone → WhatsApp | Fiteatsy client plus UI composer | PARTIAL | server-side E.164 uniqueness/provider transform not proven |
| Invitation → intake → Client360 | two intake systems | PARTIAL | overlapping token/answer ownership |
| PDF → storage → extraction → confirmation | Fiteatsy external endpoints | PARTIAL | source retention/linkage not evidenced locally |
| Confirmed biomarkers → assessment | display projection exists | BROKEN | no assessment aggregate/consumer trace |
| Measurements → calculations → plan | frontend composition | BROKEN | duplicated, unversioned calculation ownership |
| Goals/preferences/allergies → safety | visible in context | PARTIAL | publish transition does not prove snapshot binding |
| Assessment → foods → nutrients | implicit Fiteatsy intelligence/Common Food | PARTIAL | no explicit assessment version |
| Draft → review → publication | two plan lifecycles | PARTIAL | competing aggregate owners |
| Published plan → portal → reassessment | portal/history exist | PARTIAL | staleness/reassessment linkage missing |
| Availability → Google → appointment | Practice Operations foundation | PARTIAL | OAuth/runtime provider configuration unverified |

## Integrity rules

- Every key is tenant- and client-bound.
- Only confirmed observations enter clinical assessment.
- Source dates remain date-only where clinically intended; never substitute render time.
- Unknown units/nutrients remain unknown; do not coerce to zero.
- Archive/quarantine never erases legitimate confirmed history.
- Published plan versions and their assessment references are immutable.

