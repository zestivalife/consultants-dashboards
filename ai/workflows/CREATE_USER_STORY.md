# Create User Story Workflow

**Workflow ID:** AI-WF-020
**Version:** 1.0.0
**Status:** APPROVED
**Owner:** Product Architecture Office
**Classification:** Internal
**Parent:** CREATE_PRD.md

---

# Purpose

This workflow defines the enterprise standard for decomposing approved Product Requirements Documents (PRDs) into implementation-ready Epics, Features and User Stories.

It ensures all delivery work is structured, traceable, prioritised and ready for engineering execution.

No implementation SHALL begin without approved User Stories.

---

# Objectives

- Break large initiatives into manageable work.
- Maintain business traceability.
- Reduce implementation ambiguity.
- Standardise backlog creation.
- Support Agile delivery.
- Enable AI-assisted planning.
- Improve estimation accuracy.
- Improve sprint predictability.

---

# Trigger Conditions

Execute this workflow when:

- A PRD is approved.
- A new Epic enters planning.
- Product backlog refinement begins.
- Release planning starts.
- Significant change requests are approved.

---

# Required Inputs

The workflow SHALL NOT begin until the following artefacts are available:

- Approved PRD
- Approved Technical Specification
- UX Designs
- Acceptance Criteria
- Business Priorities
- Architecture Decisions
- Product Roadmap

---

# User Story Principles

Every User Story SHALL be:

- Independent
- Negotiable
- Valuable
- Estimable
- Small
- Testable

(INVEST)

---

# Story Creation Lifecycle

```
Approved PRD
      │
      ▼
Epic Definition
      │
      ▼
Feature Identification
      │
      ▼
Story Decomposition
      │
      ▼
Acceptance Criteria
      │
      ▼
Estimation
      │
      ▼
Backlog Refinement
      │
      ▼
Ready for Sprint
```

---

# Workflow Stages

## Stage 1 — Epic Definition

Owner: Product Architect

Activities:

- Review PRD.
- Identify business capabilities.
- Define Epics.
- Prioritise Epics.
- Map business value.

Output:

Epic Catalogue.

---

## Stage 2 — Feature Definition

Owner: Product Owner

Activities:

- Break Epics into Features.
- Identify dependencies.
- Define feature scope.
- Align with roadmap.

Output:

Feature Catalogue.

---

## Stage 3 — User Story Creation

Owner: Product Owner

Activities:

- Create implementation stories.
- Define personas.
- Describe expected outcomes.
- Maintain traceability.

Output:

Draft User Stories.

---

## Stage 4 — Acceptance Criteria

Owner: QA Architect

Activities:

- Write measurable acceptance criteria.
- Define success conditions.
- Identify negative scenarios.
- Validate completeness.

Output:

Acceptance Criteria.

---

## Stage 5 — Technical Review

Owner: Solution Architect

Activities:

- Review technical feasibility.
- Validate architecture.
- Identify dependencies.
- Recommend implementation sequence.

Output:

Technical Review.

---

## Stage 6 — Estimation

Owner: Engineering Team

Activities:

- Estimate effort.
- Assess complexity.
- Review implementation risks.
- Identify unknowns.

Output:

Story Estimates.

---

## Stage 7 — Backlog Refinement

Owner: Product Owner

Activities:

- Prioritise stories.
- Remove ambiguity.
- Resolve dependencies.
- Finalise sequencing.

Output:

Refined Product Backlog.

---

## Stage 8 — Approval

Owner: Product Architecture Office

Activities:

- Verify Definition of Ready.
- Review traceability.
- Approve backlog items.
- Publish stories.

Output:

Approved User Stories.

---

# Mandatory Story Structure

Every User Story SHALL include:

- Story ID
- Epic
- Feature
- Persona
- User Story Statement
- Business Value
- Description
- Acceptance Criteria
- Dependencies
- Assumptions
- Non-functional Requirements
- UX References
- API References
- Technical Notes
- Priority
- Estimate
- Definition of Ready
- Definition of Done
- Traceability Links

---

# User Story Format

Stories SHOULD follow:

As a <Persona>

I want <Capability>

So that <Business Value>

---

# Acceptance Criteria Standards

Acceptance Criteria SHOULD use:

Given

When

Then

format.

Each criterion SHALL be:

- Testable
- Unambiguous
- Independent
- Measurable

---

# Story Sizing Standards

Preferred duration:

- 1–3 engineering days.

Maximum size:

- One sprint.

Stories exceeding the maximum SHALL be decomposed further.

---

# Prioritisation Standards

Every story SHALL define:

- Business Priority
- Technical Priority
- Risk
- Customer Value
- Strategic Alignment

---

# Definition of Ready (DoR)

A story is Ready when:

- Scope is clear.
- Acceptance Criteria exist.
- Dependencies identified.
- UX available.
- Technical feasibility validated.
- Estimate completed.
- Business value defined.

---

# Definition of Done (DoD)

A story is Done when:

- Code completed.
- Tests passed.
- Documentation updated.
- Security review passed.
- Code review approved.
- Acceptance Criteria satisfied.
- Deployment successful.

---

# Traceability Standards

Every story SHALL reference:

- PRD
- Technical Specification
- Epic
- Feature
- ADR
- UX Design
- Test Cases
- Release Plan

---

# Quality Gates

The workflow SHALL pause if:

- Stories exceed agreed size.
- Acceptance Criteria are incomplete.
- Definition of Ready is unmet.
- Traceability is missing.
- Dependencies are unresolved.
- Required approvals are absent.

---

# Deliverables

Mandatory artefacts:

- Epic Catalogue
- Feature Catalogue
- User Story Backlog
- Acceptance Criteria
- Estimation Record
- Backlog Prioritisation
- Approval Record

---

# Exit Criteria

The workflow completes when:

- Stories are approved.
- Product backlog is refined.
- Traceability is complete.
- Stories satisfy Definition of Ready.
- Sprint planning can begin.

---

# Metrics

Track:

- Story Readiness
- Average Story Size
- Estimation Accuracy
- Backlog Health
- Requirement Traceability
- Story Spillover Rate
- Sprint Predictability
- Requirement Volatility

---

# Escalation

Escalate:

Business ambiguity → Product Architect

Architecture concerns → Enterprise Architect

Technical feasibility → Solution Architect

UX issues → UX Architect

Quality concerns → QA Architect

Dependency conflicts → Product Owner

---

# References

- CREATE_PRD.md
- CREATE_TECH_SPEC.md
- CREATE_ADR.md
- CREATE_TEST_PLAN.md
- BUILD_FEATURE.md
- PRODUCT_ARCHITECT.md
- SOLUTION_ARCHITECT.md
- QA_ARCHITECT.md
- AI_CONTEXT_ENGINE.md
- AI_OUTPUT_STANDARD.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Product Architecture Office | Initial User Story Creation Workflow |
