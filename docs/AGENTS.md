# AGENTS.md

## 1. Document Metadata

**Document Name:** AGENTS.md  
**Scope:** Project-wide engineering operating manual  
**Applies To:** All products, milestones, services, applications, environments, and delivery workstreams  
**Owner:** Zestiva Engineering  
**Audience:** Codex, engineers, QA, DevOps, product owners, and reviewers  
**Status:** Active  

---

## 2. Purpose

This document defines the permanent operating rules for engineering work on the Zestiva Enterprise Platform. It governs how Codex and engineers read documentation, plan work, implement changes, verify behavior, manage Git, report status, and determine whether work is complete.

This file is project-wide. It must not contain milestone-specific status, slice metadata, or temporary implementation notes.

---

## 3. Startup Sequence

Before beginning any task, read the relevant documentation in this order:

1. `DOCUMENT_REGISTRY.md`
2. `AGENTS.md`
3. `PROJECT_STATE.md`
4. `ROADMAP.md`
5. `PRD.md`
6. `TDS.md`
7. `ENGINEERING_OPERATING_MANUAL.md`
8. `DEPLOYMENT_GUIDELINES.md`
9. Active milestone documentation

If required documents are missing, stale, contradictory, or unavailable, stop and report the gap before implementation.

---

## 4. Documentation Precedence

When documents conflict, apply this precedence:

1. Product Owner decisions explicitly recorded in the current task
2. `AGENTS.md`
3. `ENGINEERING_OPERATING_MANUAL.md`
4. `PROJECT_STATE.md`
5. `ROADMAP.md`
6. `PRD.md`
7. `TDS.md`
8. Milestone implementation documents
9. Code comments and historical implementation notes

Do not silently resolve conflicts. Report the conflict, identify affected work, and wait for approval when the conflict changes architecture, scope, security, data, or production behavior.

---

## 5. Engineering Responsibilities

Codex is responsible for:

- Understanding the existing architecture before changing it.
- Protecting production behavior, data integrity, security, and user workflows.
- Implementing complete vertical slices when feature work is approved.
- Avoiding duplicate logic, duplicate services, and disconnected UI.
- Updating tests and documentation when implementation changes behavior.
- Providing evidence for verification, not assumptions.
- Preserving unrelated user or teammate changes.

---

## 6. Autonomous Execution Rules

If documentation is sufficient, implement the requested work without asking unnecessary questions.

Ask for clarification only when:

- Requirements conflict.
- The implementation choice has irreversible consequences.
- Security, data loss, compliance, or production availability may be affected.
- The requested scope is explicitly ambiguous and cannot be inferred safely.

Do not stop after analysis unless the task explicitly requests analysis only.

---

## 7. Git Workflow

The repository uses the following branch model:

- `main`: production-ready source of truth.
- `develop`: integration branch for accepted work.
- `feature/*`: new features and vertical slices.
- `bugfix/*`: non-emergency defects.
- `hotfix/*`: urgent production fixes.
- `release/*`: release preparation and stabilization.

Never commit unrelated files. Never revert changes you did not make unless explicitly instructed.

---

## 8. Branch Strategy

Create an appropriate branch before implementation unless already on a suitable branch.

Use:

- `feature/<scope>` for approved feature work.
- `bugfix/<scope>` for normal defects.
- `hotfix/<scope>` for production outages.
- `docs/<scope>` for documentation-only work.

Merge or push to `develop` only after the work meets the verification requirements for its current status.

---

## 9. Commit Policy

Use Conventional Commits:

- `feat:` for user-facing capability.
- `fix:` for defects.
- `docs:` for documentation-only changes.
- `test:` for tests.
- `refactor:` for behavior-preserving code cleanup.
- `chore:` for tooling and maintenance.
- `style:` for styling and UX-only code changes.

Each commit must be focused, explainable, and reviewable.

---

## 10. Git Synchronization Policy

Before reporting work as pushed, verify:

- Current branch.
- Latest local commit SHA.
- Working tree status.
- Remote push result.
- Whether the intended remote branch contains the commit.

If push fails, report the exact failure and do not claim synchronization.

---

## 11. Engineering Status Classification

Use only these statuses:

- `PLANNED`
- `ARCHITECTURE APPROVED`
- `IMPLEMENTATION IN PROGRESS`
- `IMPLEMENTED`
- `LOCALLY VERIFIED`
- `DEPLOYED`
- `PRODUCTION VERIFIED`
- `PRODUCTION ACCEPTED`
- `BLOCKED`

Do not invent status labels. Do not mark work complete because it builds.

---

## 12. Root Cause Analysis Policy

For defects, outages, deployment mismatches, and production failures, separate evidence from inference.

Use:

- **Observed Evidence:** Directly verified fact.
- **Inference:** Reasonable conclusion from evidence.
- **Hypothesis:** Unverified possibility requiring more evidence.

Never present a hypothesis as fact. Do not patch symptoms when the root cause is unknown.

---

## 13. Deployment Verification Policy

Deployment verification must prove that the running environment matches the intended source.

Verify where applicable:

- Git commit SHA.
- Branch.
- Deployment ID.
- Build timestamp.
- Runtime version endpoint.
- Health endpoint.
- Readiness endpoint.
- Migration version.
- Environment name.
- Service routing.
- Browser bundle version.

If production does not match source, stop feature work and diagnose deployment first.

---

## 14. Runtime Evidence Policy

Runtime verification requires evidence from the running application or service, not only source code.

Valid evidence includes:

- HTTP status and response body.
- Browser behavior.
- Console output.
- Network requests.
- Logs.
- Database records.
- Audit events.
- Notification outbox records.
- Version endpoints.
- Health/readiness endpoints.

Build success and unit tests are prerequisites, not runtime proof.

---

## 15. Regression Protection Policy

Before modifying files, identify impact across:

- Services.
- Database tables.
- API endpoints.
- Frontend pages.
- Shared libraries.
- Authentication.
- Authorization.
- Sessions.
- Routing.
- Migrations.
- Cache.
- Email.
- Notifications.

Create a regression checklist before implementation. After implementation, verify affected workflows and high-risk unrelated workflows.

---

## 16. Deployment Freeze Rule

During production incidents, deployment mismatches, authentication outages, runtime crashes, or failed acceptance gates:

- Stop new feature development.
- Do not refactor unrelated code.
- Do not add placeholder functionality.
- Focus only on restoring verified production behavior.

Resume feature work only after the blocking issue is verified resolved.

---

## 17. Version Endpoint Requirement

Every deployable service must expose a version endpoint that reports:

- Commit SHA.
- Branch.
- Build time.
- Environment.
- Service name.
- Migration version where applicable.

Version endpoints must be usable for production verification.

---

## 18. Health Endpoint Requirement

Every deployable service must expose health and readiness endpoints.

Health must confirm the process is alive. Readiness must confirm required dependencies such as database, Redis, upstream services, and required configuration are available.

---

## 19. Production Acceptance Gate

A task may be marked `PRODUCTION ACCEPTED` only when:

- The deployed environment runs the expected commit.
- Required migrations are applied.
- Browser workflow passes.
- API workflow passes.
- Database persistence is verified.
- Permissions are enforced.
- Audit events are generated for write operations.
- No relevant console errors remain.
- No relevant failed network requests remain.
- Product Owner acceptance criteria are satisfied.

---

## 20. Architecture Decision Policy

Do not redesign approved architecture during implementation.

If implementation reveals an architectural inconsistency:

1. Stop.
2. Document the inconsistency.
3. Identify affected documents and code.
4. Recommend options and trade-offs.
5. Wait for approval before changing architecture.

Approved architecture changes must be recorded in the appropriate architecture or decision document.

---

## 21. Documentation Rules

Documentation is part of the product.

Update documentation when implementation changes:

- Architecture.
- API contracts.
- Database schema.
- Workflows.
- Permissions.
- Security model.
- Deployment behavior.
- User-facing acceptance criteria.

Do not duplicate requirements across documents. Prefer cross-references to maintain a single source of truth.

---

## 22. AI Engineering Rules

Codex must:

- Read before editing.
- Prefer existing patterns.
- Use reusable platform capabilities before creating new ones.
- Avoid mock-only screens in completed work.
- Avoid disconnected buttons, routes, forms, and APIs.
- Keep implementation reversible where possible.
- Preserve accessibility, security, observability, and maintainability.
- Never expose secrets, plaintext tokens, passwords, or sensitive production data.

---

## 23. Production Reporting Standard

Final reports must include, as applicable:

- Objective.
- Files changed.
- Services affected.
- Database changes.
- API changes.
- Frontend changes.
- Tests executed.
- Runtime verification.
- Deployment version.
- Migration version.
- Commit SHA.
- Push status.
- Known issues.
- Risk level.
- Final engineering status.

Do not say “fixed,” “verified,” “production-ready,” or “live” without matching evidence.

---

## 24. Definition of Done

Work is done only when:

- Scope is implemented.
- Tests pass.
- Build passes.
- Migrations are valid.
- Runtime behavior is verified.
- Regression checklist passes.
- Documentation is updated when required.
- Code is committed.
- Code is pushed.
- Final status is accurately reported.

For feature slices, the Product Owner must be able to execute the workflow through the application UI unless explicitly approved otherwise.

---

## 25. Final Engineering Rule

Every change must leave the Zestiva Enterprise Platform more stable, more understandable, and more production-ready than before.

When speed conflicts with correctness, security, reliability, or evidence, choose correctness.
