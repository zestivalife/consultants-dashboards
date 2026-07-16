# Testing Strategy

## Purpose

Defines how Zestiva verifies correctness, stability, security, and production readiness.

## Unit Testing Standards

Unit tests cover pure business rules, validators, utilities, permissions, and service-level branching.

## Integration Testing Standards

Integration tests verify repositories, services, APIs, database behavior, transactions, and gateway contracts.

## End-to-End Testing

E2E tests cover critical user journeys across browser, API, and database persistence.

## Regression Testing

Every change needs a regression checklist based on impact analysis.

## Test Data Strategy

Use realistic personas, organizations, products, roles, permissions, packages, services, and lifecycle states.

## Test Environments

Separate local, staging/preview, and production verification. Production tests must avoid destructive data.

## Mocking Policy

Mocks are allowed in unit tests. Production UI must not rely on mock data for real workflows.

## Acceptance Testing

Acceptance requires working UI, API success, database persistence, audit logging, permissions, and browser refresh stability.

## Performance Testing

Measure page load, API latency, bundle size, query performance, and background job duration for high-risk changes.

## Security Testing

Test authentication, authorization, tenant isolation, session revocation, token expiry, input validation, and sensitive logging.

## Release Validation Matrix

| Area | Local | Production | Evidence |
| --- | --- | --- | --- |
| Build | Required | N/A | Build output |
| Tests | Required | N/A | Test summary |
| Migration | Required | Required | Migration version |
| API | Required | Required | HTTP status + body |
| Browser | Required when frontend changes | Required when deployed | Console/network results |
| Database | Required when data changes | Required when deployed | Query or service evidence |
| Security | Required for auth/access changes | Required for auth/access changes | Scenario results |
