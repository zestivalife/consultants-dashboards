# 09 Release Governance

Document ID: EDO-09  
Version: 1.0  
Status: ACTIVE  
Owner: DevOps Architecture  
Review Frequency: Every release

---

## Purpose

Define release workflow, controls and evidence requirements.

## Scope

Applies to development, QA, staging, production, rollback and hotfix releases.

## Release Workflow

```text
Development
  ↓
QA
  ↓
Staging
  ↓
Production
  ↓
Post-Release Review
```

## Release Requirements

- Version is identifiable.
- Commit SHA is known.
- Migration version is known.
- Environment variables are validated.
- Health and readiness endpoints pass.
- Gateway routing is verified.
- Rollback plan exists.
- Release notes are prepared.
- Product Owner acceptance is recorded where required.

## Hotfix Workflow

Hotfixes may bypass normal planning only for production-impacting issues.

Hotfixes still require:

- Root cause.
- Risk assessment.
- Minimal scope.
- Runtime verification.
- Post-release documentation.

## Inputs

- Completed work.
- Release checklist.
- Deployment plan.
- Test evidence.

## Outputs

- Released version.
- Rollback evidence.
- Production verification report.

## Dependencies

- Deployment Guidelines.
- Production Readiness Checklist.
- Post-Release Review.

## Success Metrics

- Deployments are traceable.
- Rollbacks are safe.
- Production drift is detected quickly.

## Risks

- Deploying wrong commit.
- Migration failure after app deployment.
- Environment mismatch.

## Related Documents

- `docs/RELEASE_CHECKLIST.md`
- `docs/governance/10_PRODUCTION_READINESS_CHECKLIST.md`
- `docs/governance/11_POST_RELEASE_REVIEW.md`

## Related ADRs

- None at creation.

