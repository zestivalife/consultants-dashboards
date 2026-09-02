# Fiteatsy Food Preference Sync Contract v1

## Scope

The Consultant Client Profile is a read-only projection of client-owned canonical facts. It must not persist a Consultant-only copy or reinterpret a preference as nutrition advice.

## Canonical ownership and transport

- Food preference profile: `health_profiles.food_preference_profile`, written through `/v1/platform/food-preferences`.
- Allergies and intolerances: `health_profiles.food_allergies` and `health_profiles.food_intolerances`, written through the canonical health-profile path.
- Authorized projection: `/v1/consultants/clients/{clientId}/workspace` after the existing assignment and role checks.
- Consultant adapter: `getFiteatsyConsultantClientProfile` maps the workspace response without truncating arrays.
- Consultant UI: the Client Profile `Food Preferences` tab presents all configured fields with truthful `Not provided` states.

## Semantic boundary

Hard constraints are diet pattern, allergies, intolerances, explicit avoids, and dietary/clinical restrictions. Soft preferences are cuisines, staple, dairy preference, preferred proteins, likes, dislikes, and practicality. Soft preferences must never be promoted to hard exclusions by this projection.

Allergy, intolerance, avoid, and dislike remain separate fields. Canonical array order is preserved. Supported enum labels are presentation-only labels for the canonical backend enum values; opaque catalogue IDs are retained in the adapter for future canonical dictionary resolution but are not rendered as names.

## Isolation and failure behaviour

Every request is scoped by canonical client identity and existing Consultant authorization. A client switch clears the prior profile before the next response is rendered. Missing or partial canonical data produces field-level empty states; it does not use mock data, another client's data, or generated recommendations.

## Regression contract

The release gate requires database-backed API parity and isolation coverage, frontend adapter/presentation coverage, the full Consultant regression suite, and a production build. Changes must preserve biomarker, Diet lifecycle, calorie/macro, and catalogue contracts.
