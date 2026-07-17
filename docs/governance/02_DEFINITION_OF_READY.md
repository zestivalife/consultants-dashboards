# 02 Definition of Ready

Document ID: EDO-02  
Version: 1.0  
Status: ACTIVE  
Owner: Enterprise Delivery Office  
Review Frequency: Monthly and during backlog refinement

---

## Purpose

Define mandatory entry criteria before engineering begins.

## Scope

Applies to all planned product, platform, architecture and operational work.

## Ready Checklist

Work is ready only when:

- Business outcome is approved.
- Product Bible alignment is confirmed.
- Architecture impact is reviewed.
- ADR need is assessed.
- PRD or equivalent requirement is approved.
- UX flow and states are defined where user-facing.
- API contract is defined where APIs are involved.
- Database ownership and migration strategy are defined where data changes exist.
- Dependencies are identified.
- Security and privacy impact is assessed.
- Permissions and audit impact are defined.
- Acceptance criteria are testable.
- Regression risks are documented.
- Rollback strategy is defined.
- Required feature flags are identified.

## Inputs

- Product request.
- Product Bible.
- PRD.
- Architecture notes.
- Risk assessment.

## Outputs

- Ready status.
- Blockers.
- Approved implementation scope.

## Dependencies

- Delivery Lifecycle.
- Architecture Review Process.
- Quality Gates.

## Success Metrics

- Fewer blocked implementation cycles.
- Fewer ambiguous acceptance criteria.
- Reduced scope churn during implementation.

## Risks

- Treating unclear work as ready causes rework.
- Excessive readiness checks may slow urgent fixes.

## Related Documents

- `docs/governance/01_DELIVERY_LIFECYCLE.md`
- `docs/governance/05_ARCHITECTURE_REVIEW_PROCESS.md`
- `docs/governance/07_QUALITY_GATES.md`

## Related ADRs

- None at creation.

