# 10 Production Readiness Checklist

Document ID: EDO-10  
Version: 1.0  
Status: ACTIVE  
Owner: Enterprise Delivery Office  
Review Frequency: Every production deployment

---

## Purpose

Provide a reusable checklist for production deployments.

## Scope

Applies to frontend, API Gateway, services, databases, background workers and infrastructure.

## Checklist

### Build and Version

- Build passed.
- Commit SHA recorded.
- Branch recorded.
- Version endpoint updated.
- Deployment ID recorded.

### Runtime

- Health endpoint returns 200.
- Readiness endpoint returns 200.
- Startup logs contain no exceptions.
- Environment variables are loaded.
- Secrets are not logged.

### Database

- Migrations applied.
- Alembic version or equivalent recorded.
- Rollback reviewed.
- Index and constraint impact reviewed.

### API and Gateway

- Gateway routes upstream correctly.
- No unexpected 5xx responses.
- CORS is correct.
- Response envelope is consistent.
- Auth and permission checks pass.

### Frontend

- Critical routes load.
- Browser refresh works.
- No console errors.
- No failed network requests.
- UI reflects mutations.

### Security

- Auth flows pass.
- Permission checks pass.
- Audit events generated.
- Sensitive data is masked.

### Operations

- Logs are structured.
- Metrics are available.
- Alerts are configured for critical paths.
- Rollback instructions are ready.

## Inputs

- Release candidate.
- Deployment logs.
- Runtime checks.
- Test evidence.

## Outputs

- Production readiness decision.
- Known issues.
- Risk rating.

## Dependencies

- Release Governance.
- Testing Strategy.
- Deployment Guidelines.

## Success Metrics

- Production acceptance is evidence-based.
- Deployment confidence improves.
- Runtime drift is detected.

## Risks

- Manual checklist fatigue.
- Missing external provider verification.

## Related Documents

- `docs/governance/09_RELEASE_GOVERNANCE.md`
- `docs/governance/08_TESTING_STRATEGY.md`
- `docs/RELEASE_CHECKLIST.md`

## Related ADRs

- None at creation.

