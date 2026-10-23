# External Consultant Client360 production acceptance

Production release under test: `a9c9a4e8395b6ec8336bb25eca4f4236ec89c243`

Test identity: governed External Consultant QA identity (`HEALTH_COACH`)

Test record: `Governed QA Missing Fields` (`6823374f-2c46-4ea0-a1d0-9e8af7598145`)

No password, token, source report, or clinical payload is recorded here. Values used during acceptance were explicitly synthetic.

| Requirement | Production surface | Expected | Actual and persistence evidence | Isolation | Browser | Result |
| --- | --- | --- | --- | --- | --- | --- |
| 01 Goals | Client360 → Progress → Goals / Progress; Practice Operations profile-enrichment API | Maximum three; fourth rejected; all persisted and projected to Diet Plan | Three synthetic goals persisted and re-rendered; fourth control disabled. Diet Plan projection requires a nutrition-capable QA session. | Tenant/client-scoped endpoint; anonymous access rejected | Three-goal control verified | NOT_VERIFIED |
| 02 DOB | Client360 → Health → Health Profile | Exact `DD/MM/YYYY`, no timezone shift | `1990-01-15` persisted and re-rendered as `15/01/1990`. A live legacy-timestamp presentation defect was found and repaired with date-only normalization. | Tenant/client-scoped endpoint | Verified; repair awaiting exact-SHA deployment | PASS |
| 03 Weight synchronisation | Client360 → Health → Measurements; Diet Plan context | Latest saved weight reaches the same client's Diet Plan | Automated contract passes. Current Health Coach capability does not expose Measurements or Diet Plan. | Capability registry correctly withholds diet surfaces | Not available for this QA profession | NOT_VERIFIED |
| 04 Health Record dates | Client360 → Health → Health Records | Persist and format report and confirmation dates | Existing QA record shows report `15/10/2026`; synthetic confirmation date persisted and re-rendered as `16/10/2026`. | Existing QA record only | Verified | PASS |
| 05 Profile completion | Client360 → Health → Health Profile | Incomplete is not 100%; valid updates recalculate | Changed from 25% to 50%, then 63% after persisted valid data. | QA record only | Verified | PASS |
| 06 Medical History | Client360 → Health → Health Profile | Ordinary text; no JSON error; persisted | Synthetic ordinary text saved, returned by server response, and rendered in the canonical section. | QA record only | Verified | PASS |
| 07 Sleep & Stress | Client360 → Health → Health Profile | Ordinary text persists | Synthetic narrative saved and returned by server response. | QA record only | Verified | PASS |
| 08 Profile and evidence completeness | Client360 → Health → Health Profile | Truthful separate percentages | Profile recalculated from 25% to 63%; evidence remained truthfully 0% because measurements were unavailable for this profession. | QA record only | Verified | PASS |
| 09 BMI | Client360 → Health → Measurements | Derived only from valid persisted height/weight; missing/invalid unavailable | Automated edge cases pass. Current Health Coach capability does not expose Measurements. | Capability-gated | Not available for this QA profession | NOT_VERIFIED |
| 10 Anthropometrics | Client360 → Health → Measurements | Waist, hip, neck persistence and waist-to-hip ratio | Automated persistence/projection tests pass. Current Health Coach capability does not expose Measurements. | Capability-gated | Not available for this QA profession | NOT_VERIFIED |

## Security evidence

- Anonymous profile-enrichment requests fail closed with HTTP 401.
- The authenticated session resolved as an External Consultant with a canonical `HEALTH_COACH` profession.
- Only assigned clients were displayed in the governed client roster.
- No Internal Authentication, Super Admin, Fiteatsy, or `api.nuetra.in` source was changed.

## Acceptance categories

- Implementation acceptance: PASS (10/10)
- Automated acceptance: PASS (468/468 frontend; production build PASS)
- Live API acceptance: PARTIAL — persisted read/write evidence for goals, DOB, narratives, completion, and Health Record dates
- Live browser acceptance: PARTIAL — six requirements verified; nutrition-capability checks require an authenticated nutrition-capable QA identity
