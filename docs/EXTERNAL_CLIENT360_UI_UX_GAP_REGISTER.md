# External Client360 UI/UX Gap Register

| ID | Priority | Surface | Current behavior | Defect / user impact | Recommended External-only fix | Acceptance |
|---|---|---|---|---|---|---|
| UI-01 | P0 | Reports | Upload/review UI exists | A legacy upload path can simulate values; users cannot distinguish canonical ingestion by code presence alone | Remove legacy path from External routing; label canonical processing and provenance | No External request can reach simulated processor |
| UI-02 | P0 | Nutrition | Biomarkers, assessment-like intelligence, and plan editor are separate | No visible immutable assessment/version explains plan inputs | Assessment summary drawer with source/date/review/version and stale state | Every plan displays assessment version and evidence |
| UI-03 | P0 | Documents/Health Records | Separate lists and owners | Confirmed biomarkers may coexist with “No historical documents” | Unified read model referencing source object and extraction/record IDs; truthful missing-source state | No false empty; missing source is explicit without deleting observations |
| UI-04 | P1 | Overview | Identity and completion warnings are composed from multiple payloads | Visible name/mobile can still be flagged missing | Server-projected normalized completion with per-field provenance | Visible canonical value cannot be simultaneously missing |
| UI-05 | P1 | Measurements | BMI/WHR shown from frontend calculation | Method/version absent and possible drift | Render server calculation result and method metadata | Reload-stable values match assessment context |
| UI-06 | P1 | Biomarkers | Strong review/history UI | Upload entry point is not consistently co-located | Add PDF-only “Upload lab report” action that calls canonical document ingestion | PDF MIME + signature enforced; no image option |
| UI-07 | P1 | Health Profile | Client and consultant data can appear together | Attribution/version boundaries are not always evident | Visually separate “Client reported” and “Professional assessment” with timestamps | Consultant cannot silently overwrite client facts |
| UI-08 | P1 | Nutrition readiness | Draft and publish actions exist | Missing data may either silently pass or over-block | Explicit states: Information required, Ready, Review required, Draft permitted, Publication blocked | Safe drafts allowed; unsafe publish denied server-side |
| UI-09 | P1 | Diet Plan | Rich Common Food editor | Duplicate plan APIs make state ownership opaque | Route all UI state through one canonical plan adapter | One plan ID/version across draft, reload, publish, portal, DOCX |
| UI-10 | P1 | Progress | Generic progress views exist | No clear assessment/plan-version context | Label measurement/biomarker/adherence series with source and plan version | Trend points have source and date |
| UI-11 | P1 | WhatsApp | Deep-link sharing exists | Phone normalization and delivery failure truth not proven | E.164 display; provider transform server-side; explicit delivery/open state | Country code preserved; no PHI/token leak in URL text |
| UI-12 | P1 | Calendar | Google/Microsoft schema/UI foundation | Product target is Google only and credentials may be unconfigured | Hide new Microsoft connection; preserve history; show configured/reauth/error states | Google connect/sync/reschedule/cancel verified live |
| UI-13 | P2 | Biomarker trends | History exists | Clinical relevance to assessment is implicit | Explain “considered/not considered” with assessment reference, no diagnosis language | Traceable and reviewable |
| UI-14 | P2 | Mobile | Responsive tests exist | Full authenticated long-form/editor acceptance absent | Physical 360/390/414 matrix | No horizontal page scroll; touch targets pass |

## Route/component inventory

- External shell: `nuetra-frontend/components/external/ExternalConsultantWorkspace.jsx`
- Client360 composition: `ExternalClient360.jsx`, `ProfessionClient360.jsx`
- Health intake/profile: `ExternalClientHealthIntake.jsx`, `ExternalClientProfileEnhancements.jsx`
- Biomarkers: `ExternalBiomarkerReview.jsx`, `ExternalBiomarkerHistory.jsx`
- Health Records/report: `ExternalHealthRecords.jsx`, `ExternalTransientReportAnalyzer.jsx`
- Diet Plan: `ExternalMultiDietPlan.jsx`, `ExternalDietPlanHistory.jsx`, platform `CommonFoodPlanEditor.jsx`
- Calendar: `ExternalCalendarWorkspace.jsx`
- Communication: `ExternalCommunicationWorkspace.jsx`
- Public client portal: `pages/client-portal/[token].js`

## State-quality finding

Automated tests explicitly protect loading, error, restricted, confirmed-empty, and false-zero states. Authenticated production behavior was not exercised, so these are `AUTOMATED_TEST_PASS`, not `LIVE_BROWSER_VERIFIED`.

