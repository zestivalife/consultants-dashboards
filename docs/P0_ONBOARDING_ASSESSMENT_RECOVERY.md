# P0 onboarding and assessment checkpoint

## Confirmed release regressions

| Surface | Failing contract | Confirmed cause | Correction |
|---|---|---|---|
| Owner → Fiteatsy Leads | `GET /api/v1/platform/fiteatsy/leads` | Gateway delegated to `/v1/internal/delegated/intake-leads`, which was absent from the deployed Fiteatsy release lineage. The non-JSON 404 became `FITEATSY_INVALID_RESPONSE`. | Restore the signed delegated intake-lead route and its filtered, paginated repository query. |
| Owner → Client Assignments | `/api/v1/platform/fiteatsy/professional-assignments/*` | The frontend shipped before its Gateway bridge and Fiteatsy delegated assignment routes. | Restore the signed Gateway operations and tenant-aware Fiteatsy assignment routes. |
| Consultant workspace registration | `/v1/internal/delegated/external-consultant-signups/provision` | Auth called a Fiteatsy provisioning route excluded from the production release line. | Restore idempotent signup, tenant OWNER membership, profile and resumable onboarding provisioning. |
| External workspace Add Client | `POST /v1/external/clients` | The frontend called a legacy Fiteatsy route; Practice Operations was already authoritative for the client directory but exposed only GET. | Add tenant-scoped `POST /api/v1/practice-operations/clients` and route the active workspace/lead conversion through it. |

## Canonical assessment field reuse

The client remains the source for client-submitted facts. A consultant assessment may confirm or professionally interpret them, but must not silently overwrite the original response.

| Domain | Fiteatsy/mobile source | Zestiva intake/assessment key | Handling |
|---|---|---|---|
| Dietary preference | `dietType` / onboarding nutrition | `dietary_preference` | Reuse; normalize `EGGITARIAN` to `EGG`; preserve source provenance. |
| Food likes/dislikes | verified food IDs, disliked/avoided foods | `food_dislikes_preferences` | Reuse verified IDs/labels; do not convert preferences into allergies. |
| Allergies/intolerances | `foodAllergies`, `foodIntolerances` | `allergy_status`, `food_allergies`, `allergies_intolerances` | Reuse; consultant confirmation is independent. |
| Restrictions | dietary/religious restrictions | `food_restrictions` | Reuse; keep distinct from dislike and allergy. |
| Meal pattern | meals/day, meal timing, skipped meals, typical intake | `meal_timing_frequency`, `typical_dietary_intake`, `appetite_eating_patterns` | Reuse when present; request only missing fields. |
| Hydration | water intake | `water_intake` | Reuse with unit conversion and provenance. |
| Medical conditions | structured conditions and medical history | `nutrition_medical_conditions` | Reuse only within consented clinical scope. |
| Medication/supplements | medication and supplement lists | `relevant_medications`, `relevant_supplements` | Reuse; consultant may confirm relevance without changing client source. |
| Goals | wellness/weight goals | `weight_management_goals`, `recovery_disease_management_goals` | Reuse and split by governed goal taxonomy. |
| Body context | height, weight, goal weight, waist/hip | measurement/profile context | Reuse latest eligible dated measurements; not duplicated into questionnaire answers. |
| Lifestyle | occupation, work routine, activity, sleep/stress | profile context; selective information request where registered | Reuse existing profile values. Only registry-approved missing fields may be requested. |
| Consultant notes | none | `consultant_notes` | Consultant-only interpretation; never represented as client-submitted. |

The selective-information registry is server versioned. Its approved client-editable fields are dietary preference, allergy status, food allergies, food restrictions, meal frequency, typical intake, appetite/eating patterns, water intake, medical conditions, medications, supplements and health goals. Links carry opaque tokens and field identifiers only. Submitted answers remain pending consultant review where clinically required.

## Authority boundaries

- Auth resolves identity and active tenant membership.
- Practice Operations owns consultant-created client records, invitations, assessment workflow and workspace directory projection.
- Fiteatsy owns registered mobile identities and their canonical health/onboarding data.
- Gateway validates the session and delegates signed, operation-scoped calls; it does not fabricate memberships or assignments.
- Assignment controls directory visibility. Consent independently controls protected health data.
- Retries use idempotency keys; duplicate contact or active assignment conflicts return explicit `409` responses.
