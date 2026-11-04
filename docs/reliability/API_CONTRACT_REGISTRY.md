# API contract registry and compatibility rules

Authoritative machine-readable file:

`nuetra-frontend/contracts/external-consultant-api-registry.json`

Initial scope covers the ten production-critical External Consultant workflows and the delegated health-context dependency. This is the first increment, not a claim that every platform route is registered.

## Required contract fields

Every registry entry identifies:

- frontend workflow and component;
- API client wrapper;
- browser-facing method and endpoint;
- Gateway or proxy boundary;
- owning service and service endpoint;
- authentication and authorization boundary;
- database or downstream dependency;
- request and response schema authority;
- expected status codes;
- source markers used by automated compatibility checks.

The registry references existing source schemas and handlers. It does not create new request or response contracts.

## Enforced compatibility rules

`nuetra-frontend/tests/api-contract-registry.test.mjs` fails when:

1. a required contract field is missing;
2. a contract ID or browser operation is duplicated;
3. an unsupported HTTP method or invalid status code is registered;
4. a registered frontend component or API client disappears;
5. a registered route/function marker is removed or renamed;
6. any of the ten critical workflows loses coverage;
7. the policy preserving legitimate 400, 401, 403 and 404 responses changes silently.

Because the test is included by `node --test tests/*.test.mjs`, it runs in exact-SHA CI.

## Compatibility workflow

For a deliberate breaking change:

1. identify every registered consumer;
2. add backward-compatible server handling or a versioned endpoint;
3. add provider and consumer contract tests;
4. update the registry and migration strategy in the same reviewable commit;
5. pass exact-SHA CI and integrated staging before production approval.

Removing a marker merely to make the registry test pass is prohibited. The source endpoint, consumer and compatibility strategy must agree.

## Confirmed gaps requiring later increments

- Full route discovery and registration for non-critical Consultant modules remains incomplete.
- Python service OpenAPI documents are generated at runtime but are not yet snapshotted and diffed in CI.
- Fiteatsy Express routes do not publish one consolidated OpenAPI document.
- Gateway rewrite/upstream compatibility is not yet generated from the same registry.
- Response schemas for several legacy endpoints are implicit in handlers rather than named schemas.
- Real cross-service provider/consumer tests require an isolated staging environment and synthetic identities.
- Timeout, 502 and 504 behavior is registered for delegated dependencies but not yet executed in integrated staging.

## Next safe increments

1. Generate a discovered route inventory for Gateway and every Python service, then fail on unreviewed registry drift.
2. Add OpenAPI snapshots and compatibility diffing for schema-bearing services.
3. Register the remaining frontend modules in bounded domain batches.
4. Execute provider/consumer contracts against isolated databases and real service processes.
5. Add immutable build provenance and Docker-context validation before any release image is produced.
