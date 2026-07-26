# AGENTS.md

## 1. Document Metadata

**Document Name:** AGENTS.md  
**Scope:** Project-wide engineering operating manual  
**Applies To:** All Zestiva products, applications, services, environments, milestones, and delivery workstreams  
**Owner:** Zestiva Engineering  
**Audience:** AI agents, engineers, QA, DevOps, product owners, and reviewers  
**Status:** Active  

---

## 2. Purpose

This document defines the permanent operating rules for engineering work on the Zestiva Enterprise Platform.

It governs how agents and engineers read documentation, analyze requests, implement changes, verify behavior, manage Git, report production readiness, and determine whether work is complete.

This file is project-wide. It must not contain milestone-specific status, slice metadata, or temporary implementation notes.

---

## 3. Startup Sequence

Before beginning any task, complete the repository startup sequence.

Read documentation in this order:

1. `docs/index/DOCUMENT_REGISTRY.md`
2. `AGENTS.md`
3. `docs/delivery/PROJECT_STATE.md`
4. `docs/delivery/ROADMAP.md`
5. Relevant `PRD.md`
6. Relevant `TDS.md`
7. Relevant `ENGINEERING_OPERATING_MANUAL.md`
8. Relevant `DEPLOYMENT_GUIDELINES.md`
9. Relevant architecture documentation
10. Relevant platform capability documentation
11. Relevant domain documentation
12. Relevant service documentation
13. Active milestone documentation
14. Current task

When the repository contains an AI operating system under `ai/` or `.ai/`, read its operating rules before analysis or implementation and load only documents relevant to the task.

If required documents are missing, stale, contradictory, or unavailable, stop and report the gap before implementation.

---

## 4. Documentation Precedence

When documents conflict, apply this precedence:

1. Product Owner decisions explicitly recorded in the current task
2. `AGENTS.md`
3. AI operating rules under `ai/` or `.ai/`, when present
4. `docs/index/DOCUMENT_REGISTRY.md`
5. `docs/index/SOURCE_OF_TRUTH_MATRIX.md`
6. Governance documentation
7. Repository architecture documentation
8. Enterprise architecture documentation
9. Platform capability documentation
10. Domain documentation
11. Product documentation
12. Service documentation
13. Milestone documentation
14. Code comments and historical implementation notes

Do not silently resolve conflicts. Report conflicts, identify affected work, and wait for approval when a conflict changes architecture, scope, security, data, or production behavior.

---

## 5. Engineering Responsibilities

Agents and engineers are responsible for:

- Understanding the existing architecture before changing it.
- Protecting production behavior, data integrity, security, privacy, accessibility, observability, and user workflows.
- Implementing complete vertical slices when feature work is approved.
- Avoiding duplicate logic, duplicate services, disconnected UI, and temporary architecture.
- Updating tests and documentation when implementation changes behavior.
- Providing evidence for verification, not assumptions.
- Preserving unrelated user, teammate, or generated changes.
- Leaving the platform more stable and understandable than before.

---

## 6. Autonomous Execution Rules

If documentation is sufficient, proceed with the requested work without unnecessary questions.

Ask for clarification only when:

- Requirements conflict.
- The implementation choice has irreversible consequences.
- Security, data loss, compliance, or production availability may be affected.
- The requested scope is ambiguous and cannot be inferred safely from repository evidence.

Do not stop after analysis unless the task explicitly requests analysis only, architecture only, documentation only, or no code changes.

---

## 7. Git Workflow

The repository uses this branch model:

- `main`: production-ready source of truth.
- `develop`: integration branch for accepted work.
- `feature/*`: new features and vertical slices.
- `bugfix/*`: non-emergency defects.
- `hotfix/*`: urgent production fixes.
- `release/*`: release preparation and stabilization.

Never commit unrelated files. Never revert changes you did not make unless explicitly instructed.

---

## 8. Branch Strategy

Create or use an appropriate branch before implementation unless already on a suitable branch.

Use:

- `feature/<scope>` for approved feature work.
- `bugfix/<scope>` for normal defects.
- `hotfix/<scope>` for production incidents or urgent production blockers.
- `release/<scope>` for release stabilization.
- `docs/<scope>` for documentation-only work.

Merge or push to `develop` only after the work satisfies the verification requirements for its current engineering status.

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

Do not mix unrelated implementation, documentation, formatting, and deployment changes in one commit.

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

For defects, outages, deployment mismatches, runtime crashes, failed acceptance gates, and production failures, separate evidence from interpretation.

Use:

- **Observed Evidence:** Directly verified fact.
- **Inference:** Reasonable conclusion from evidence.
- **Hypothesis:** Unverified possibility requiring more evidence.

Never present a hypothesis as fact. Do not patch symptoms when the root cause is unknown.

When investigating a defect, trace the complete execution path instead of stopping at the first suspicious line.

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
- Docker image or build artifact identity.
- Service routing.
- Browser bundle version.

If production does not match source, stop feature work and diagnose deployment before changing application logic.

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
- Health and readiness endpoints.

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
- Background jobs.
- Deployment and runtime configuration.

Create a regression checklist before implementation. After implementation, verify affected workflows and high-risk unrelated workflows.

---

## 16. Deployment Freeze Rule

During production incidents, deployment mismatches, authentication outages, authorization failures, runtime crashes, or failed acceptance gates:

- Stop new feature development.
- Do not refactor unrelated code.
- Do not add placeholder functionality.
- Focus only on restoring verified production behavior.

Resume feature work only after the blocking issue is verified resolved.

---

## 17. Version Endpoint Requirement

Every deployable service must expose a version endpoint that reports:

- Service name.
- Commit SHA.
- Branch.
- Build time.
- Environment.
- Deployment ID where available.
- Migration version where applicable.
- Release identifier where available.

Version endpoints must be usable for production verification.

---

## 18. Health Endpoint Requirement

Every deployable service must expose health and readiness endpoints.

Health must confirm the process is alive.

Readiness must confirm required dependencies are available, including database, Redis, upstream services, required configuration, and critical external providers where applicable.

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
- Notification or outbox behavior is verified when relevant.
- No relevant console errors remain.
- No relevant failed network requests remain.
- Product Owner acceptance criteria are satisfied.

Do not claim production acceptance from local build, unit tests, or source inspection alone.

---

## 20. Architecture Decision Policy

Do not redesign approved architecture during implementation.

If implementation reveals an architectural inconsistency:

1. Stop.
2. Document the inconsistency.
3. Identify affected documents and code.
4. Recommend options and trade-offs.
5. Wait for approval before changing architecture.

Approved long-term architecture changes must be recorded in the appropriate architecture document or Architecture Decision Record.

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

Do not create new governance documents unless explicitly requested or required by the approved documentation architecture.

---

## 22. AI Engineering Rules

Agents must:

- Read before editing.
- Prefer existing patterns.
- Use reusable platform capabilities before creating new ones.
- Avoid role-specific exceptions unless explicitly approved.
- Avoid mock-only screens in completed work.
- Avoid disconnected buttons, routes, forms, and APIs.
- Keep implementation reversible where possible.
- Preserve accessibility, security, observability, and maintainability.
- Never expose secrets, plaintext tokens, passwords, or sensitive production data.

Agents must not:

- Guess.
- Hallucinate APIs, fields, migrations, or runtime behavior.
- Duplicate authorization logic.
- Hardcode business behavior that belongs in configuration or policy.
- Hide uncertainty.

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
