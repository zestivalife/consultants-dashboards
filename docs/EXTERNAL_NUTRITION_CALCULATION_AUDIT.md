# External Nutrition Calculation Audit

## Inventory

| Calculation | Current owner/evidence | Method | Validation | Versioning | Finding |
|---|---|---|---|---|---|
| Age | client/base projections | date-derived or supplied age; no canonical implementation found in active External path | inconsistent | none visible | P1: derive server-side from DOB/date and retain DOB provenance |
| BMI | `nuetra-frontend/lib/externalClientProfile.mjs:20-25` | kg / m², rounded 1 decimal | positive height/weight | none | P0 duplicate/presentation-owned |
| WHR | same file:27-30 | waist / hip, rounded 2 decimals | positive waist/hip | none | P0 duplicate/presentation-owned |
| Health BMI score | `scoring-engine-service/.../health_score.py:11-24` | range penalty | height/weight present | algorithm field exists on score record | Separate wellness scoring, not Diet Plan target methodology |
| Energy target | Fiteatsy nutrition intelligence or consultant input | formula not present in this repo | insufficient evidence | not visible in client plan contract | P0 untraceable methodology |
| Protein target | Fiteatsy intelligence or consultant input | formula not present | numeric contract | not visible | P0 untraceable methodology |
| Plan actual totals | Practice Operations `main.py:1204-1211` | sums option kcal/protein | option payload numeric | snapshot per version | Partial; duplicates Fiteatsy authoritative totals |
| Common Food nutrients | Fiteatsy `/common-food/*` | server-owned catalogue/serving calculation | stale/version/safety errors tested | plan version IDs | Strong source contract, frozen dependency |
| Intake completion | Practice Operations `main.py:1764` | answered / available questions ×100 | required check at submit | instance version/audit | Working for profession intake only |
| Progress rates | Practice Operations generic progress | domain-dependent | source type fields | no assessment linkage | P1 for nutrition monitoring |

## Duplications and defects

1. BMI is a frontend-derived display value and also an input to scoring formulas.
2. Practice Operations and Fiteatsy both model diet plans and totals.
3. The legacy nutrition service accepts calorie/macronutrient targets without deriving or versioning methodology.
4. The legacy Profile Service report processor produces random biomarker values; these are not calculations and must never be treated as extraction.
5. No repository-level implementation of a governed REE/TDEE methodology was found in the active External path.
6. No central rounding/unit policy covers clinical measurements, targets, and nutrient totals.

## Required calculation contract

An External-owned calculation result should contain: method code and version, input IDs/versions, units, population applicability, exclusions, raw result, display result, rounding rule, calculated time, actor/system source, warnings, and missing-input state.

Required behavior:

- Never derive energy/macronutrient targets when required inputs are absent.
- Keep calculations advisory and consultant-reviewed.
- Preserve raw precision; round only defined output fields.
- Unit-normalize before formula execution.
- Recalculate to a new assessment version; never mutate historical results.
- Frontend must render server results rather than independently recompute clinical truth.

## Regression plan

- Metric/imperial conversion boundaries and impossible values.
- DOB/date-only age boundaries and leap years.
- BMI/WHR exact formula/version and missing-input states.
- REE/TDEE methodology population/exclusion matrix after clinical methodology approval.
- Macro gram/kcal reconciliation and rounding invariants.
- Common Food serving replacement, combination, and stale-plan concurrency.
- Confirmed versus unconfirmed biomarker inclusion.
- Assessment staleness after each input domain changes.
- Cross-client and cross-tenant denial for every calculation request.

