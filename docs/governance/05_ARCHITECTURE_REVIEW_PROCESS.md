# 05 Architecture Review Process

Document ID: EDO-05  
Version: 1.0  
Status: ACTIVE  
Owner: Enterprise Architecture  
Review Frequency: Monthly and before material architectural changes

---

## Purpose

Define the workflow for reviewing architecture before implementation.

## Scope

Applies to new capabilities, service changes, data ownership changes, security-impacting changes and cross-product decisions.

## Required Questions

Every architecture review must answer:

- What is the business impact?
- What is the architecture impact?
- What is the platform impact?
- What is the security impact?
- What is the future scalability impact?
- Does this capability already exist?
- Can this be solved through configuration?
- Does this require a new service?
- Does this affect database ownership?
- Does this affect APIs?
- Does this affect permissions?
- Does this affect navigation, dashboards or workflows?
- Does this affect other products?
- Is an ADR required?

## Review Outcomes

- Approved.
- Approved with constraints.
- Rework required.
- Blocked pending Product Owner decision.
- ADR required before implementation.

## Inputs

- Product request.
- Product Bible.
- Current architecture docs.
- Impact analysis.

## Outputs

- Architecture review decision.
- ADR requirement.
- Constraints and risks.

## Dependencies

- Product Bible.
- ZEPO Operating Model.
- Document Registry.

## Success Metrics

- Fewer conflicting service boundaries.
- Fewer duplicated capabilities.
- Architecture decisions are traceable.

## Risks

- Skipping ADRs for long-lived decisions.
- Treating implementation convenience as architecture approval.

## Related Documents

- `docs/ZESTIVA_ONE_PLATFORM_BLUEPRINT.md`
- `docs/product-bible/APPENDICES/ZEPO_OPERATING_MODEL.md`
- `docs/governance/07_QUALITY_GATES.md`

## Related ADRs

- Create ADRs when review changes platform direction, service boundaries, data ownership or security posture.

