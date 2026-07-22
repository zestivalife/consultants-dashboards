# MASTER_ENGINEERING_EXECUTION_PROTOCOL.md

Version: 1.0
Status: APPROVED
Lifecycle: ACTIVE
Owner: Product & Engineering
Applies To: Entire Zestiva One Platform

---

# 1. PURPOSE

This document defines the mandatory engineering execution protocol for all AI agents, engineers, and contributors working on the Zestiva One Platform.

Its purpose is to ensure:

- Consistent engineering practices
- Enterprise-grade software quality
- Production-first thinking
- Safe deployments
- Stable releases
- Maintainable architecture
- Complete production verification

Every milestone, feature, enhancement, bug fix, refactor, or hotfix must comply with this protocol.

---

# 2. ENGINEERING PHILOSOPHY

The platform shall be developed according to the following principles:

- Runtime is the source of truth.
- Production correctness is more important than implementation completion.
- Root causes must always be resolved instead of symptoms.
- Platform stability takes precedence over new features.
- Engineering decisions must favour maintainability over shortcuts.
- Security is mandatory, not optional.
- Every change must be verifiable.
- Every release must be reproducible.
- Every deployment must be observable.

---

# 3. DOCUMENT READING ORDER

Before implementing any work, engineers or AI agents must review the following documents in order:

1. MASTER_ENGINEERING_EXECUTION_PROTOCOL.md
2. PLATFORM_OPERATIONS_SPECIFICATION.md
3. RELEASE_ENGINEERING_SPECIFICATION.md
4. IAM_CAPABILITY_ENGINE_SPECIFICATION.md
5. Product Puran
6. Governance Documents
7. Current Milestone Specification
8. Current Task

Implementation must never contradict higher-level documents.

---

# 4. ENGINEERING OWNERSHIP

The executing AI assumes responsibility as:

- Chief Software Architect
- Principal Product Architect
- Principal Backend Engineer
- Principal Frontend Engineer
- Principal IAM Engineer
- Principal Security Engineer
- Principal DevOps Engineer
- Principal QA Engineer
- Principal Release Engineer
- Site Reliability Engineer (SRE)

The AI owns the end-to-end delivery of the assigned scope.

---

# 5. IMPLEMENTATION PRINCIPLES

The AI shall:

- Understand the complete business objective.
- Analyse all impacted modules.
- Identify dependencies.
- Identify architectural implications.
- Review existing implementations.
- Avoid duplicate logic.
- Reuse existing services whenever appropriate.
- Preserve backward compatibility unless explicitly approved.
- Produce maintainable and readable code.
- Update documentation when architecture changes.

---

# 6. ROOT CAUSE ANALYSIS POLICY

Never implement superficial fixes.

For every issue:

1. Identify the symptom.
2. Determine the root cause.
3. Collect evidence.
4. Implement the correct fix.
5. Add regression tests.
6. Verify the repair.
7. Confirm no regressions exist.

Engineering reports must always distinguish between symptoms and root causes.

---

# 7. SELF-HEALING EXECUTION

During implementation, if additional issues are discovered, the AI must:

- Investigate the issue.
- Assess impact.
- Repair the issue if it falls within the affected scope.
- Update tests.
- Continue implementation.

The AI must not intentionally leave known defects unresolved without documenting them.

---

# 8. PLATFORM STABILIZATION POLICY

Feature development shall pause whenever any of the following exist:

- Critical authentication failures
- Authorization failures
- Data corruption
- Platform instability
- Gateway failures
- Service unavailability
- Failed production migrations
- Critical security issues

Platform stability takes priority over feature delivery.

---

# 9. RUNTIME-FIRST VERIFICATION

Never assume correctness from:

- Repository state
- Previous reports
- Documentation
- Local testing alone

The only authoritative validation is the running production environment.

Verification must include:

- Running APIs
- Running services
- Gateway behaviour
- UI behaviour
- Database state
- Production logs
- Health endpoints

If runtime differs from documentation, runtime takes precedence until corrected.

---

# 10. TESTING POLICY

Every implementation must include appropriate testing.

Minimum expectations:

- Unit Tests
- Integration Tests
- API Tests
- Security Validation
- Smoke Tests

When applicable:

- End-to-End Tests
- Performance Tests
- Regression Tests

No implementation should reduce existing test coverage without explicit approval.

---

# 11. SECURITY POLICY

Every implementation must respect:

- Authentication
- Authorization
- Principle of Least Privilege
- Tenant isolation
- Secure password handling
- Input validation
- Output sanitization
- Audit logging
- Secure session management

Security issues are always treated as high priority.

---

# 12. DEPLOYMENT POLICY

Implementation is not considered complete until deployment has been verified.

For every modified service:

- Build
- Container creation
- Deployment
- Migration
- Startup
- Health verification
- Readiness verification
- Runtime verification
- Business verification

Repository state alone is insufficient evidence of completion.

---

# 13. PRODUCTION VERIFICATION

Every release must verify:

- GitHub commit
- Running commit
- Health endpoints
- Readiness endpoints
- Version endpoints
- Gateway connectivity
- Database migrations
- Authentication
- Authorization
- Business workflows

Production verification is mandatory.

---

# 14. RELEASE STATE CLASSIFICATION

Every engineering task must conclude with exactly one release state.

## PLATFORM READY

Conditions:

- Production deployed
- Platform healthy
- Business workflows verified
- No blocking issues remain

---

## DEPLOYMENT PENDING

Conditions:

- Implementation complete
- Tests passed
- Code merged
- Awaiting deployment or runtime update

This is an operational state, not a technical failure.

---

## PLATFORM BLOCKED

Conditions:

A genuine technical issue prevents production readiness.

Examples:

- Authentication failure
- Authorization failure
- Database migration failure
- Platform unavailable
- Critical service failure
- Business workflow failure

---

# 15. SEVERITY CLASSIFICATION

## P0

Business-critical functionality unavailable.

Blocks release.

---

## P1

Security, authentication, or authorization failure.

Blocks release.

---

## P2

Critical platform health or infrastructure issue.

Blocks release.

---

## P3

Operational visibility or observability issue.

Does not block release unless explicitly required.

---

## P4

Developer tooling, documentation, or code quality improvement.

Does not block release.

---

# 16. QUALITY STANDARDS

Every implementation must be:

- Readable
- Modular
- Testable
- Maintainable
- Secure
- Observable
- Documented
- Backward compatible where applicable

---

# 17. CHANGE MANAGEMENT

Before implementation:

- Identify affected services.
- Identify affected APIs.
- Identify affected database schema.
- Identify affected UI.
- Identify documentation updates.

After implementation:

- Update tests.
- Update documentation if required.
- Verify production.

---

# 18. REGRESSION PREVENTION

Every resolved defect should include:

- Root cause
- Permanent fix
- Regression test
- Verification evidence

The same issue should not recur due to missing automated validation.

---

# 19. REPORTING FORMAT

Every engineering execution report shall include:

1. Executive Summary
2. Scope of Work
3. Root Cause Analysis
4. Architecture Impact
5. Services Modified
6. APIs Modified
7. Database Changes
8. Files Modified
9. Test Results
10. Deployment Status
11. Production Verification
12. Risks
13. Recommendations
14. Release State

---

# 20. ACCEPTANCE CRITERIA

Work is considered complete only when:

- All required implementation is finished.
- Tests pass.
- Documentation is updated where necessary.
- Deployment is successful.
- Production verification succeeds.
- Acceptance criteria are met.
- The final release state has been declared.

---

# 21. CONTINUOUS IMPROVEMENT

This protocol is a living engineering standard.

Enhancements should:

- Improve reliability
- Improve maintainability
- Improve observability
- Improve security
- Improve deployment confidence
- Improve developer productivity

Changes to this protocol require review and approval by Product & Engineering leadership.
