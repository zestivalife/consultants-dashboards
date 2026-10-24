# MP-010 canonical intake mapping

This audit records the existing 14 client-facing health-intake sections in
`ExternalClientHealthIntake.jsx`. The source remains the existing intake/profile
payload; MP-010 adds only request lifecycle metadata and does not create a second
copy of captured clinical answers.

| Step | Existing form keys | Validation/applicability | Canonical consumer |
|---|---|---|---|
| About you | `aboutYou.dateOfBirth`, `gender`, contact, occupation, location | DOB/gender required; identity/contact governed upstream | Client360 profile |
| Medical history | `medicalHistory.hadSurgery`, hospitalisation, treatment | Conditional detail after Yes | Client360 health context |
| Conditions & symptoms | `conditionsSymptoms.conditions`, symptoms, frequency | Explicit negative choices preserved | Nutrition medical context |
| Allergies & family history | `allergiesFamilyHistory.hasAllergies`, types, `foodAllergies`, notes, family history | Allergy detail conditional on Yes | Assessment allergies/restrictions |
| Medications & supplements | `medicationsSupplements.takesMedication`, `medications`, `takesSupplements`, `supplementTypes`, notes | Conditional repeatable medicines | Assessment medications/supplements |
| Lifestyle | tobacco, alcohol, caffeine, work schedule | Optional governed enumerations | Client360 lifestyle |
| Sleep & stress | duration, quality, concerns, times, stress | Optional governed enumerations | Client360 lifestyle |
| Activity & hydration | activity, exercise, `waterIntakeMl` | Exercise detail conditional; zero is not treated as blank by resolver | Assessment water/lifestyle |
| Nutrition | `dietPreference`, `restrictions`, intolerances, `mealsPerDay`, `skipMeals`, meals/snacks | Compatibility rules retained | NutritionProfile fields |
| Goals | `goals.goals`, primary goal, notes | Goal and priority required | Assessment goals |
| Measurements | height, weight, waist, hip, BP, pulse, glucose | Units/ranges validated by measurement owner | MP-006 measurement context |
| Women's health | menstrual status, cycle, symptoms, date | Female applicability only | Client360 health context |
| Reports & documents | PDF health records | PDF validation and transient extraction unchanged | Health Records / confirmed biomarkers |
| Review & consent | review, consent and submit | Consent required for full intake | Intake status and provenance |

## MP-010 selective field registry

The versioned `FIELD_REGISTRY` maps client-answerable assessment inputs to the
existing payload paths and NutritionProfile destinations. Consultant-only
review state, targets, calculations and professional conclusions are excluded.
Responses use field-level patch semantics, preserve unrelated answers, record
`CLIENT_FOLLOW_UP` provenance, and remain pending professional review.

The External-only migration `external_0056_smart_intake_requests` adds only:

- request metadata and hashed opaque-token scope;
- versioned draft/submission patches;
- append-only lifecycle audit events.

It does not modify Internal Consultant, Auth, Fiteatsy, food-engine, published
plans, or existing health-record/biomarker schemas.
