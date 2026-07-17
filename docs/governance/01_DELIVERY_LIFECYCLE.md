# 01 Delivery Lifecycle

Document ID: EDO-01  
Version: 1.0  
Status: ACTIVE  
Owner: Enterprise Delivery Office  
Review Frequency: Monthly or before each release train

---

## Purpose

Define how Zestiva One Platform turns business intent into governed, verified, production-ready delivery.

## Scope

Applies to every product, capability, milestone, slice, hotfix and platform change.

## Lifecycle

```text
Business Idea
  ↓
Product Bible
  ↓
Architecture
  ↓
ADR
  ↓
PRD
  ↓
UX Specification
  ↓
API Contract
  ↓
Database Design
  ↓
Implementation
  ↓
Testing
  ↓
Release
  ↓
Operations
  ↓
Continuous Improvement
```

## Stage Expectations

| Stage | Required Outcome |
|---|---|
| Business Idea | Problem, audience, business value and success metric are clear |
| Product Bible | Capability, product and platform alignment are documented |
| Architecture | Domain ownership, service boundaries and risks are reviewed |
| ADR | Material architecture decisions are recorded |
| PRD | Requirements, rules and acceptance criteria are approved |
| UX Specification | Journeys, states, accessibility and information architecture are defined |
| API Contract | Request, response, errors, auth and versioning are specified |
| Database Design | Ownership, migrations, indexes, constraints and rollback are defined |
| Implementation | Approved scope is built as a vertical slice |
| Testing | Unit, integration, contract, E2E, security and regression checks pass |
| Release | Version, migration, deployment and rollback are verified |
| Operations | Health, readiness, logs, metrics and support paths are monitored |
| Continuous Improvement | Post-release learning feeds Product Bible, backlog and ADRs |

## Inputs

- Product Bible.
- Document Registry.
- Roadmap.
- PRD and TDS.
- ADRs.
- Release Checklist.

## Outputs

- Approved delivery plan.
- Verified implementation.
- Release evidence.
- Post-release learning.

## Dependencies

- ZEPO Operating Model.
- Architecture Review Process.
- Quality Gates.
- Release Governance.

## Success Metrics

- Reduced rework.
- Fewer production regressions.
- Clear traceability from idea to release.
- Every release has runtime evidence.

## Risks

- Skipping architecture creates platform debt.
- Over-documenting small changes slows delivery.
- Missing validation allows production regressions.

## Related Documents

- `docs/product-bible/APPENDICES/ZEPO_OPERATING_MODEL.md`
- `docs/governance/02_DEFINITION_OF_READY.md`
- `docs/governance/03_DEFINITION_OF_DONE.md`
- `docs/governance/07_QUALITY_GATES.md`

## Related ADRs

- None at creation.

