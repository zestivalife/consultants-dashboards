# RELEASE_ENGINEERING_SPECIFICATION.md

Version: 1.0
Status: APPROVED
Lifecycle: ACTIVE
Owner: Platform Engineering
Applies To: All Repositories, Services and Deployments

---

# 1. PURPOSE

This specification defines the Release Engineering standards for the Zestiva One Platform.

Its objectives are to ensure:

- Reliable deployments
- Reproducible releases
- Standardised verification
- Production consistency
- Controlled rollbacks
- Deployment traceability
- Enterprise-grade operational governance

Every deployment must comply with this specification.

---

# 2. RELEASE PHILOSOPHY

A release is not considered complete when code is merged.

A release is complete only when:

✓ Production is deployed

✓ Production is verified

✓ Business workflows pass

✓ Runtime matches the expected release

Repository state alone is never considered sufficient evidence.

---

# 3. BRANCHING STRATEGY

Permanent Branches

main

Production-ready code only.

develop

Integration branch for completed features.

Feature Branches

feature/<feature-name>

Hotfix Branches

hotfix/<issue-name>

Release Branches (optional)

release/<version>

---

# 4. RELEASE LIFECYCLE

Business Requirement

↓

Architecture Review

↓

Implementation

↓

Code Review

↓

Unit Testing

↓

Integration Testing

↓

Merge to develop

↓

Validation

↓

Merge to main

↓

Build

↓

Deploy

↓

Production Verification

↓

Release Approval

↓

PLATFORM READY

---

# 5. BUILD STANDARDS

Every build must:

- Complete successfully
- Generate a deployable artifact
- Include version metadata
- Embed Git commit information
- Record build timestamp
- Preserve semantic version

Failed builds shall never proceed to deployment.

---

# 6. DEPLOYMENT STANDARDS

Each deployment shall verify:

- Image creation
- Image publication
- Container startup
- Migration execution
- Configuration loading
- Secret validation
- Health endpoint
- Readiness endpoint
- Version endpoint

Deployment is incomplete until runtime verification succeeds.

---

# 7. PRODUCTION VERIFICATION

Every production deployment shall verify:

Repository Commit

↓

Running Commit

↓

Build Version

↓

Migration Version

↓

Deployment Identifier

↓

Health

↓

Readiness

↓

Gateway Connectivity

↓

Authentication

↓

Authorization

↓

Business Smoke Tests

Every step must succeed.

---

# 8. RELEASE STATES

Exactly one release state shall be declared.

## PLATFORM READY

Conditions:

- Deployment complete
- Verification complete
- No blocking defects
- Business workflows operational

---

## DEPLOYMENT PENDING

Conditions:

- Implementation complete
- Tests passed
- Code merged
- Awaiting deployment or runtime update

This is an operational state.

It is not a technical failure.

---

## PLATFORM BLOCKED

Conditions:

A genuine technical issue prevents production readiness.

Examples:

- Authentication failure
- Gateway failure
- Migration failure
- Critical service unavailable
- Business workflow failure

---

# 9. SEVERITY MATRIX

## P0 – Critical

Business-critical workflow unavailable.

Release blocked.

---

## P1 – Security

Authentication, authorization or security issue.

Release blocked.

---

## P2 – Platform

Gateway, database or infrastructure issue.

Release blocked.

---

## P3 – Operational

Observability, runtime metadata or monitoring issue.

Release permitted unless explicitly required.

---

## P4 – Improvement

Documentation, tooling or code quality enhancement.

Release permitted.

---

# 10. ROLLBACK POLICY

Rollback shall occur when:

- Production instability detected
- Critical regression introduced
- Migration failure
- Security issue
- Business workflow broken

Rollback must restore the last verified production release.

---

# 11. RELEASE CHECKLIST

Before deployment verify:

✓ Unit tests

✓ Integration tests

✓ API tests

✓ Security checks

✓ Code review

✓ Documentation updates

Before approval verify:

✓ Health

✓ Ready

✓ Version

✓ Gateway

✓ Authentication

✓ Authorization

✓ Business workflows

✓ Smoke tests

---

# 12. SMOKE TESTS

Minimum production smoke tests:

Platform Owner Login

Corporate Admin Login

Practitioner Login

JWT Validation

/api/v1/auth/me

People & Access

Gateway Routing

Health Endpoints

Ready Endpoints

Version Endpoints

Critical API Calls

---

# 13. VERSION STANDARD

Every deployed service shall expose:

service

version

release

commit

build_time

deployment

migration

environment

Optional:

commit_sha

deployment_id

migration_version

---

# 14. RELEASE TRACEABILITY

Every release shall be traceable using:

- Git commit
- Semantic version
- Build timestamp
- Deployment identifier
- Migration version
- Environment
- Release identifier

This information must be available at runtime.

---

# 15. DEPLOYMENT AUDIT

Every deployment shall record:

- Who initiated the deployment
- When deployment started
- When deployment completed
- Build version
- Commit
- Target environment
- Result
- Rollback status

---

# 16. FAILURE RECOVERY

When deployment fails:

1. Stop rollout.
2. Identify root cause.
3. Preserve logs.
4. Roll back if required.
5. Verify production.
6. Record incident.
7. Update regression tests if applicable.

---

# 17. CONTINUOUS DEPLOYMENT PRINCIPLES

Deployment pipelines should be:

- Repeatable
- Deterministic
- Observable
- Automated where practical
- Safe to retry
- Safe to roll back

---

# 18. RELEASE APPROVAL

A release may only be approved when:

- Production verification succeeds
- Required smoke tests pass
- No unresolved P0, P1 or P2 issues exist
- Release state is PLATFORM READY

If deployment has not yet reached production:

Release state shall be:

DEPLOYMENT PENDING

---

# 19. REPORTING FORMAT

Every release report shall include:

1. Executive Summary
2. Services Deployed
3. Files Modified
4. Commits Included
5. Database Changes
6. Tests Executed
7. Deployment Verification
8. Production Verification
9. Risks
10. Rollback Status
11. Release State

---

# 20. CONTINUOUS IMPROVEMENT

Release Engineering standards shall evolve to improve:

- Deployment confidence
- Verification quality
- Rollback safety
- Release traceability
- Automation
- Operational efficiency
- Platform reliability

Changes to this specification require Product & Engineering approval.
