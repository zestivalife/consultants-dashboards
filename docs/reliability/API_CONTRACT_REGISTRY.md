# Executable API contract registry

Machine-readable authorities:

- `nuetra-frontend/contracts/external-consultant-api-registry.json` — consumer requirements for the ten critical workflows.
- `nuetra-frontend/contracts/provider-route-inventory.json` — versioned provider operations, Gateway prefixes and required response fields.

The cross-repository portion is pinned to Fiteatsy `f7762c1eed4c3026913028742655d6c3f5a6e38e`. The Consultant provider inventory is pinned to the reliability baseline and verified against the imported FastAPI application at test time.

## Mandatory checks

`nuetra-frontend/tests/api-contract-registry.test.mjs` performs deterministic compatibility comparison. It fails for an absent provider operation, HTTP method mismatch, missing required response field, absent Gateway mapping or absent registered consumer operation. Independent negative mutation fixtures prove that route removal, method change and response-field removal are rejected.

`services/practice-operations-service/tests/test_critical_api_contract_inventory.py` obtains the real registered FastAPI routes from `app.routes` and compares canonical path plus method against the inventory. It also checks the real Gateway configuration contains every required prefix and that the Fiteatsy equivalent contract snapshot is bound to the verified SHA.

The existing database-backed client-directory and diet-plan lifecycle suites exercise response envelopes and lifecycle fields against PostgreSQL. The versioned inventory makes consumed response fields explicit so removal is a compatibility failure rather than an undocumented implementation change.

## Actual discovery result

The earlier marker registry incorrectly listed `/v1/external/clients` and `/v1/external/clients/{clientId}/360` as registered Fiteatsy endpoints. Fiteatsy `f7762c1…` registers neither route. The active connected-client flow is:

`ExternalClient360` → Gateway `/api/v1/practice-operations` → Practice Operations connection health-context → delegated Fiteatsy `/v1/internal/external-consultant-access/{userId}/health-context`.

The unconnected legacy fallback remains recorded under `known_incompatible_consumers`; it is not counted as covered. Repairing or removing that fallback requires a separate behavior decision because no verified provider contract exists for it.

## Change policy and remaining boundary

Any deliberate breaking change must update provider implementation, consumer, inventory and positive/negative tests together. Editing only the snapshot to hide drift is prohibited. Production deployment, database migration and schema stamping are outside this increment.

Fiteatsy Express does not expose consolidated OpenAPI. Its two critical provider operations are represented by an equivalent versioned contract pinned to the verified Fiteatsy SHA. A future cross-repository CI job should regenerate it from the Fiteatsy route tree when repository credentials are available; this increment does not claim all Fiteatsy routes are covered.
