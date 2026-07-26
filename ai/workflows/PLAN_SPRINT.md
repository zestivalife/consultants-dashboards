# Sprint Planning Workflow

**Workflow ID:** AI-WF-025
**Version:** 1.0.0
**Status:** APPROVED
**Owner:** Engineering Management Office
**Classification:** Internal
**Parent:** CREATE_TASK.md

---

# Purpose

This workflow defines the enterprise standard for planning engineering sprints.

Sprint Planning converts a prioritised engineering backlog into a realistic, achievable Sprint Backlog by balancing business priorities, engineering capacity, dependencies, technical readiness and delivery risk.

Every sprint SHALL begin with an approved Sprint Plan.

---

# Objectives

- Maximise delivery predictability.
- Balance engineering capacity.
- Prioritise business value.
- Validate Definition of Ready.
- Reduce sprint spillover.
- Coordinate cross-functional teams.
- Enable AI-assisted workload allocation.
- Improve release confidence.

---

# Trigger Conditions

Execute this workflow when:

- A new sprint begins.
- Sprint backlog refinement is complete.
- Capacity changes significantly.
- Emergency work requires replanning.
- Product priorities change.

---

# Required Inputs

The workflow SHALL NOT begin until the following artefacts are available:

- Approved Product Backlog
- Approved User Stories
- Approved Engineering Tasks
- Team Capacity
- Sprint Goal Proposal
- Release Plan
- Dependency Register
- Engineering Metrics

---

# Sprint Planning Principles

Every Sprint SHALL be:

- Goal driven
- Capacity based
- Business aligned
- Technically feasible
- Risk aware
- Measurable
- Traceable
- Adaptable

---

# Sprint Planning Lifecycle

```
Sprint Goal
      │
      ▼
Capacity Planning
      │
      ▼
Backlog Selection
      │
      ▼
Dependency Review
      │
      ▼
Risk Assessment
      │
      ▼
Commitment
      │
      ▼
Sprint Start
```

---

# Workflow Stages

## Stage 1 — Sprint Goal Definition

Owner: Product Owner

Activities:

- Define sprint objective.
- Align with roadmap.
- Confirm business priorities.
- Identify expected outcomes.
- Validate strategic alignment.

Output:

Sprint Goal.

---

## Stage 2 — Capacity Planning

Owner: Engineering Manager

Activities:

- Review team availability.
- Account for leave and holidays.
- Review support commitments.
- Review technical debt allocation.
- Calculate available engineering capacity.

Output:

Capacity Plan.

---

## Stage 3 — Backlog Selection

Owner: Product Owner

Activities:

- Select highest priority work.
- Validate business value.
- Verify dependencies.
- Confirm implementation sequence.
- Remove blocked items.

Output:

Sprint Backlog.

---

## Stage 4 — Technical Validation

Owner: Solution Architect

Activities:

- Review technical readiness.
- Validate dependencies.
- Confirm architecture alignment.
- Verify implementation feasibility.
- Identify technical risks.

Output:

Technical Validation Report.

---

## Stage 5 — AI & Resource Allocation

Owner: Engineering Manager

Activities:

- Assign work to engineers.
- Allocate AI coding agents.
- Define pair programming tasks.
- Identify review ownership.
- Balance workload.

Output:

Resource Allocation Plan.

---

## Stage 6 — Risk Assessment

Owner: Release Manager

Activities:

- Identify delivery risks.
- Assess dependency risks.
- Review external blockers.
- Assess production impact.
- Define mitigation actions.

Output:

Sprint Risk Register.

---

## Stage 7 — Sprint Commitment

Owner: Scrum Master

Activities:

- Review sprint backlog.
- Confirm team commitment.
- Validate sprint goal.
- Finalise sprint scope.
- Publish Sprint Plan.

Output:

Approved Sprint Plan.

---

# Mandatory Sprint Plan Structure

Every Sprint Plan SHALL include:

- Sprint ID
- Sprint Name
- Sprint Goal
- Sprint Duration
- Start Date
- End Date
- Product Goal Alignment
- Selected Epics
- Selected Features
- Selected User Stories
- Selected Tasks
- Team Members
- AI Agent Assignments
- Capacity Plan
- Risk Register
- Dependencies
- Sprint Metrics
- Success Criteria
- Definition of Done
- Approval Record
- Revision History

---

# Capacity Planning Standards

Capacity calculations SHALL include:

- Working days
- Leave
- Public holidays
- Support rotations
- Meetings
- Planned technical debt
- Innovation allocation
- Buffer for unplanned work

---

# Backlog Selection Standards

Selection SHALL prioritise:

- Business value
- Customer impact
- Risk reduction
- Strategic alignment
- Dependency order
- Release commitments
- Technical debt

---

# AI Assignment Standards

Every Sprint SHALL identify:

- Human-owned tasks
- AI-owned tasks
- Hybrid implementation tasks
- AI review tasks
- Documentation automation
- Test automation

---

# Definition of Ready Validation

Each selected backlog item SHALL satisfy:

- Approved User Story
- Approved Tasks
- Acceptance Criteria
- Technical feasibility
- UX readiness
- Test strategy
- Dependencies resolved

---

# Risk Assessment Standards

Review:

- Technical risks
- Operational risks
- Resource risks
- External dependencies
- Vendor dependencies
- Production constraints

---

# Sprint Success Metrics

Track:

- Sprint Goal Achievement
- Velocity
- Throughput
- Story Completion Rate
- Task Completion Rate
- Spillover Rate
- Defect Escape Rate
- AI Productivity
- Review Time
- Cycle Time

---

# Quality Gates

The workflow SHALL pause if:

- Sprint capacity exceeded.
- Definition of Ready unmet.
- Critical dependencies unresolved.
- Team commitment unavailable.
- Sprint Goal unclear.
- Required approvals missing.

---

# Deliverables

Mandatory artefacts:

- Sprint Plan
- Sprint Backlog
- Capacity Plan
- Risk Register
- Resource Allocation Plan
- Sprint Commitment Record

---

# Exit Criteria

The workflow completes when:

- Sprint Goal approved.
- Sprint Backlog committed.
- Capacity validated.
- Dependencies accepted.
- Sprint officially starts.

---

# Escalation

Escalate:

Business priority conflicts → Product Owner

Architecture concerns → Solution Architect

Capacity constraints → Engineering Manager

Delivery risks → Release Manager

Agile process issues → Scrum Master

Executive priority conflicts → Product Steering Committee

---

# References

- CREATE_TASK.md
- CREATE_USER_STORY.md
- CREATE_FEATURE.md
- CREATE_EPIC.md
- CREATE_RELEASE_PLAN.md
- BUILD_FEATURE.md
- RELEASE_MANAGER.md
- ENGINEERING_MANAGER.md
- AI_EXECUTION_ENGINE.md
- AI_OUTPUT_STANDARD.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Engineering Management Office | Initial Sprint Planning Workflow |
