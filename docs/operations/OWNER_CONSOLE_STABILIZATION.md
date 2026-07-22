# Owner Console Stabilization

## Scope

This sprint refactors the Platform Owner console without changing business behavior. The focus is maintainability, route-backed state preservation, and reusable UI foundations for future modules across Nuetra, FitEatsy, and future Zestiva products.

## Frontend improvements

- Extracted shared owner-console UI primitives into:
  - `nuetra-frontend/components/platform/OwnerConsolePrimitives.jsx`
- Extracted People & Access orchestration into:
  - `nuetra-frontend/hooks/useOwnerPeopleAccess.js`
- Kept route state behavior unchanged:
  - URL-backed filters
  - selected user preservation
  - shallow routing for secondary state

## Why this matters

Before this pass, `OwnerConsoleModules.jsx` and `OwnerConsolePage.jsx` both mixed rendering concerns with orchestration logic. That made each new module or People & Access change riskier and increased the cost of basic maintenance.

After this pass:

- visual primitives are reusable
- People & Access API coordination lives in one hook
- route-backed module rendering remains intact
- future owner-console modules can reuse the same shared shell instead of duplicating controls

## Shared foundations introduced

- `ModuleFrame`
- `ActionButton`
- `ControlBar`
- `Badge`
- `Panel`
- `StatPill`
- `MiniBarChart`
- `EmptyState`

## Remaining debt

- `OwnerConsoleModules.jsx` is still oversized and should be split by module area in a later stabilization pass
- some legacy non-owner dashboard files still coexist with the newer owner-console architecture
- `lib/api.js` and `utils/api.js` should be reviewed for overlap before new API work continues
