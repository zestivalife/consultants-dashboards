# Fiteatsy Common Food Consultant UI v17.4

The Consultant client drawer integrates the Common Food Combination Engine through the existing Fiteatsy API abstraction. The backend remains authoritative for client eligibility, option nutrition, serving constraints, persistence, concurrency, and lifecycle snapshots.

## Activation

The supported V1 surface is enabled by default. Set `NEXT_PUBLIC_COMMON_FOOD_COMBINATION_ENGINE_V1=false` in the Consultant frontend deployment to invoke the explicit legacy-editor rollback switch.

Supported V1 profiles are Vegetarian, Egg-inclusive, and Non-vegetarian. Vegan generation remains fail-closed through the backend capability response.

## Workflow

1. Use the single `Generate Diet Plan` action to create or refresh a persisted draft and generate the seven common-food meal heads.
2. Work in the single Diet Plan editor. Common-food and legacy authoring surfaces are mutually exclusive; the legacy editor remains available only through the rollback branch.
3. Review the backend coverage status and option details.
4. Save generated options as server-validated snapshots.
5. Use Food Explorer to add or replace components or change governed servings.
6. Reload to verify the persisted snapshot, then submit through the existing lifecycle controls.
7. Senior Consultants review the frozen combination snapshot; existing change-request, approval, publish, and backend DOCX actions remain authoritative.

## Production route contract

The Consultant proxy forwards Common Food requests to `/v1/consultants/clients/:clientId/...`. The retired `/v1/consultants/nutrition/clients/:clientId/...` proposal is not a deployed backend route and must not be reintroduced.

The frontend never calculates authoritative option nutrition. Unknown fibre and other nutrient values remain `null` and render as `Not reported`.

## Rollback

Set `NEXT_PUBLIC_COMMON_FOOD_COMBINATION_ENGINE_V1=false` and restore the previous Vercel deployment if necessary. Legacy and mixed plans remain readable; the accepted backend migrations are additive.
