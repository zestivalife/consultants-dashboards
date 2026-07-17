# 03 Definition of Done

Document ID: EDO-03  
Version: 1.0  
Status: ACTIVE  
Owner: Enterprise Delivery Office  
Review Frequency: Monthly and before release acceptance

---

## Purpose

Define mandatory completion criteria before work can be marked complete.

## Scope

Applies to all milestones, slices, bug fixes, documentation updates and platform changes.

## Done Checklist

Work is done only when:

- Approved scope is implemented.
- Product Bible impact is addressed.
- Architecture remains internally consistent.
- ADRs are created or updated where required.
- Documentation is updated.
- Changelog is updated.
- APIs are compatible or versioned.
- Database migrations are safe and reversible where possible.
- Tests pass for affected layers.
- Security impact is reviewed.
- Accessibility is verified for UI changes.
- Audit and notification requirements are implemented where applicable.
- Release notes are prepared.
- Runtime evidence is collected for deployed work.
- Production readiness checklist passes where production is affected.
- Known limitations are documented.
- Product Owner acceptance criteria are satisfied.

## Inputs

- Ready checklist.
- Implementation.
- Test results.
- Runtime evidence.

## Outputs

- Completion report.
- Release evidence.
- Updated documentation.

## Dependencies

- Release Checklist.
- Testing Strategy.
- Production Readiness Checklist.

## Success Metrics

- Completed work is demonstrable.
- Production regressions decrease.
- Documentation and implementation remain aligned.

## Risks

- Marking work done based only on build success.
- Missing runtime verification for deployed changes.

## Related Documents

- `docs/RELEASE_CHECKLIST.md`
- `docs/governance/08_TESTING_STRATEGY.md`
- `docs/governance/10_PRODUCTION_READINESS_CHECKLIST.md`

## Related ADRs

- None at creation.

