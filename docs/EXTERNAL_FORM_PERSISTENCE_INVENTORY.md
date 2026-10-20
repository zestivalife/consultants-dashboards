# External Consultant form persistence inventory

This inventory records the External-only persistence audit performed for the multi-Diet Plan and profile repair. It does not reopen Internal, Common Food, biomarker-observation, or Client Core contracts.

| Surface | Save contract | Durable store | Reload proof | Failure behavior |
|---|---|---|---|---|
| Marketplace public profile | `PUT /marketplace/profile` | `external_consultant_public_profile_versions` | Refetch and exact projection comparison | No success state when server projection differs |
| Marketplace phone | `PUT /marketplace/contact` | `external_consultant_contact_profiles` | Refetch returns E.164 | Country-aware validation; 422 on invalid number |
| Marketplace photo | prepare → object upload → finalise | governed object storage + `external_consultant_profile_photos` | Refetch published proxy URL | Pending upload never becomes current until object verification |
| Client Diet Plans | `POST /external/clients/:id/diet-plans` | `external_diet_plans` + versions | List/refetch by client and selected plan ID | 400/409/422 shown; no false saved state |
| Client Diet Plan draft | `PUT /diet-plans/:planId/draft` | selected plan version only | Plan list reloaded after save | Stale version rejected |
| Diet Plan publish | `POST /diet-plans/:planId/publish` | exact selected version | Plan list reloaded with published status | Explicit confirmation; incomplete plan rejected |

Other External forms remain on their existing governed endpoints. This change does not alter onboarding, consultations, follow-ups, goals, tasks, documents, health records, biomarker review, packages, billing, or portal persistence. Their existing source and regression suites remain authoritative; no success simulation or local-only storage was introduced.

Validation boundaries are identical client/server contracts: plan name 2–120 characters, daily calories 800–6000 kcal, daily protein 20–400 g, JPEG/PNG profile photo up to 5 MiB, and country-aware E.164 telephone parsing.
