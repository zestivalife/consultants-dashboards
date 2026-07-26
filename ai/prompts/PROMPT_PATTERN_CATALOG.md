# Enterprise Prompt Pattern Catalog

**Document ID:** AI-PROMPT-004

**Version:** 1.0.0

**Status:** APPROVED

**Owner:** Enterprise AI Platform Architecture Office

**Classification:** Enterprise Prompt Pattern Standard

**Parent:** PROMPT_TEMPLATE_LIBRARY.md

---

# Purpose

The Enterprise Prompt Pattern Catalog defines the canonical prompt engineering patterns used throughout the Enterprise AI Operating System (EAIOS).

Rather than creating prompts from scratch, engineers, AI agents and applications SHALL compose prompts using reusable cognitive patterns that encapsulate proven reasoning techniques, business logic and governance controls.

Prompt Patterns are reusable architectural assets.

---

# Objectives

The Enterprise Prompt Pattern Catalog SHALL:

- Standardise prompt engineering.
- Promote reusable cognitive patterns.
- Improve reasoning quality.
- Reduce prompt duplication.
- Enable adaptive prompt composition.
- Improve explainability.
- Support multi-model optimisation.
- Accelerate AI solution delivery.
- Improve governance.
- Increase prompt maintainability.

---

# Scope

This catalog applies to:

- AI Assistants
- Digital Employees
- Enterprise Agents
- Copilots
- Business Applications
- Multi-Agent Systems
- Workflow Engines
- Enterprise APIs
- AI Development Teams

---

# Pattern Principles

## Principle 1 — Intent Before Syntax

Patterns SHALL describe business intent rather than prompt wording.

---

## Principle 2 — Composable

Patterns SHALL combine with other patterns.

---

## Principle 3 — Vendor Independent

Patterns SHALL remain independent of foundation model implementation.

---

## Principle 4 — Governed

Patterns SHALL be approved before production usage.

---

## Principle 5 — Observable

Pattern performance SHALL be measurable.

---

## Principle 6 — Evolvable

Patterns SHALL continuously improve through analytics.

---

# Enterprise Pattern Architecture

```text
Business Objective
        │
        ▼
Pattern Selection
        │
        ▼
Pattern Composition
        │
 ┌──────┼─────────┐
 ▼      ▼         ▼
Role  Knowledge  Policies
 │      │         │
 ▼      ▼         ▼
Memory Runtime Context
        │
        ▼
Execution Prompt
        │
        ▼
LLM
```

---

# Pattern Classification

Enterprise Prompt Patterns SHALL be organised into:

- Cognitive Patterns
- Business Patterns
- Workflow Patterns
- Decision Patterns
- Collaboration Patterns
- Knowledge Patterns
- Evaluation Patterns
- Security Patterns
- Governance Patterns
- Communication Patterns

---

# Cognitive Patterns

## Sequential Reasoning

Purpose:

Break complex problems into ordered reasoning steps.

Use Cases:

- Planning
- Troubleshooting
- Root Cause Analysis
- Multi-stage Decisions

---

## Tree Reasoning

Purpose:

Explore multiple solution branches before selecting the best outcome.

Use Cases:

- Strategic Planning
- Architecture
- Design Exploration
- Innovation

---

## Reflective Reasoning

Purpose:

Evaluate intermediate reasoning before producing the final answer.

Use Cases:

- Quality Review
- Risk Assessment
- Verification

---

## Comparative Reasoning

Purpose:

Compare multiple alternatives against defined criteria.

Use Cases:

- Vendor Selection
- Product Evaluation
- Trade-off Analysis

---

## Constraint-Based Reasoning

Purpose:

Optimise solutions within predefined business or technical constraints.

Use Cases:

- Budget Planning
- Scheduling
- Resource Allocation

---

# Business Patterns

Standard business patterns include:

- Business Analysis
- Requirement Discovery
- Stakeholder Mapping
- Opportunity Assessment
- Value Stream Analysis
- Business Case Development

---

# Workflow Patterns

Supported workflows:

- Customer Onboarding
- Incident Management
- Change Management
- Release Management
- Product Discovery
- Software Delivery
- Compliance Review

---

# Decision Patterns

Decision patterns include:

- Weighted Decision Matrix
- Cost-Benefit Analysis
- Risk Matrix
- Priority Matrix
- Multi-Criteria Evaluation
- Recommendation Framework

---

# Knowledge Patterns

Knowledge patterns include:

- Retrieval-Augmented Generation
- Citation Generation
- Knowledge Synthesis
- Context Expansion
- Evidence Validation
- Multi-Source Verification

---

# Collaboration Patterns

Patterns include:

- Agent Delegation
- Consensus Building
- Expert Consultation
- Task Negotiation
- Workflow Coordination
- Escalation

---

# Evaluation Patterns

Evaluation SHALL support:

- Quality Assessment
- Architecture Review
- Code Review
- UX Review
- Security Review
- Compliance Review

---

# Governance Patterns

Governance SHALL include:

- Policy Validation
- Risk Assessment
- Approval Workflow
- Regulatory Review
- Audit Evidence
- Exception Handling

---

# Security Patterns

Security patterns include:

- Prompt Injection Defence
- Output Validation
- Secret Protection
- Data Classification
- Privacy Validation
- Trust Verification

---

# Communication Patterns

Communication patterns include:

- Executive Summary
- Technical Documentation
- Meeting Notes
- Status Reporting
- Email Generation
- Presentation Creation

---

# Pattern Metadata

Every pattern SHALL define:

- Pattern ID
- Pattern Name
- Category
- Description
- Business Objective
- Inputs
- Outputs
- Dependencies
- Constraints
- Owner
- Version
- Status

---

# Pattern Composition

Patterns MAY compose with:

- Role Patterns
- Capability Patterns
- Workflow Patterns
- Knowledge Patterns
- Evaluation Patterns
- Governance Patterns

Composition SHALL preserve governance requirements.

---

# Pattern Selection Criteria

Selection SHALL consider:

- Business Objective
- User Intent
- Agent Capability
- Available Knowledge
- Runtime Context
- Model Capability
- Cost
- Governance Policies

---

# Pattern Registry

The Enterprise Pattern Registry SHALL maintain:

- Pattern Catalogue
- Pattern Versions
- Pattern Dependencies
- Owners
- Usage Statistics
- Evaluation Scores
- Approval History
- Retirement Status

---

# Pattern Lifecycle

Patterns SHALL progress through:

1. Proposal
2. Design
3. Validation
4. Approval
5. Publication
6. Adoption
7. Optimisation
8. Deprecation
9. Retirement

---

# Pattern Metrics

Track:

- Usage Frequency
- Reuse Rate
- Success Rate
- Business Value
- Response Quality
- Token Efficiency
- Latency
- User Satisfaction
- Cost per Execution

---

# Governance

The Enterprise Prompt Pattern Catalog SHALL be governed by:

- Chief AI Architect
- Prompt Engineering Team
- AI Governance Board
- Enterprise Architecture Board

Pattern reviews SHALL occur quarterly.

---

# Quality Gates

A pattern SHALL fail validation if:

- Business objective is undefined.
- Pattern owner is missing.
- Dependencies are undocumented.
- Governance approval is absent.
- Security review is incomplete.
- Evaluation criteria are undefined.

---

# Deliverables

Mandatory artefacts include:

- Pattern Catalogue
- Pattern Specifications
- Pattern Registry
- Dependency Graph
- Validation Reports
- Governance Records
- Analytics Dashboard

---

# Success Metrics

Track:

- Pattern Adoption
- Pattern Reuse Rate
- Prompt Quality Improvement
- Engineering Productivity
- Governance Compliance
- Response Consistency
- Token Optimisation
- Business Value Generated
- User Satisfaction

---

# References

- PROMPT_ARCHITECTURE.md
- PROMPT_LIFECYCLE.md
- PROMPT_TEMPLATE_LIBRARY.md
- PROMPT_REGISTRY.md
- PROMPT_GOVERNANCE.md
- PROMPT_SECURITY.md
- AI_OPERATING_MODEL.md
- QUALITY_GATES.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise AI Platform Architecture Office | Initial Enterprise Prompt Pattern Catalog |
