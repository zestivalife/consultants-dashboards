# 07 Quality Gates

Document ID: EDO-07  
Version: 1.0  
Status: ACTIVE  
Owner: Enterprise Delivery Office  
Review Frequency: Every milestone and release

---

## Purpose

Define mandatory quality gates before work may proceed.

## Scope

Applies to all platform capabilities, product work, milestones and releases.

## Mandatory Gates

| Gate | Required Check |
|---|---|
| Business | Business value and success metrics are clear |
| Product | Product scope and acceptance criteria are approved |
| UX | Journeys, states and accessibility are covered |
| Architecture | Platform alignment and service boundaries are approved |
| Engineering | Implementation follows standards and avoids duplication |
| Security | Auth, permissions, secrets, privacy and abuse cases are reviewed |
| QA | Test coverage and regression plan are defined and executed |
| Documentation | Registry, changelog, Product Bible and ADRs are updated |
| Operations | Deployment, rollback, monitoring and support are ready |

## Gate Outcomes

- Pass.
- Pass with risk accepted.
- Rework required.
- Blocked.

## Inputs

- Delivery plan.
- Review evidence.
- Test results.
- Runtime evidence.

## Outputs

- Gate decision.
- Risks.
- Required corrective actions.

## Dependencies

- Definition of Ready.
- Definition of Done.
- Architecture Review Process.
- Production Readiness Checklist.

## Success Metrics

- No milestone proceeds with known blocking gaps.
- Release confidence improves.
- Production incidents decrease.

## Risks

- Gate bypass during urgency.
- Gates becoming checkbox-only without evidence.

## Related Documents

- `docs/governance/02_DEFINITION_OF_READY.md`
- `docs/governance/03_DEFINITION_OF_DONE.md`
- `docs/governance/10_PRODUCTION_READINESS_CHECKLIST.md`

## Related ADRs

- None at creation.

