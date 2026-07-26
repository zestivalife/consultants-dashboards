# Enterprise Prompt Template Library

**Document ID:** AI-PROMPT-003

**Version:** 1.0.0

**Status:** APPROVED

**Owner:** Enterprise AI Platform Architecture Office

**Classification:** Enterprise Prompt Standard

**Parent:** PROMPT_ARCHITECTURE.md

---

# Purpose

The Enterprise Prompt Template Library defines the standard catalogue of reusable prompt templates used throughout the Enterprise AI Operating System (EAIOS).

The library enables consistent, governed and reusable prompt engineering by providing standardised templates for common business, operational and technical use cases.

Every enterprise prompt SHALL originate from an approved template.

---

# Objectives

The Enterprise Prompt Template Library SHALL:

- Standardise prompt creation.
- Encourage reuse.
- Reduce prompt duplication.
- Improve prompt quality.
- Accelerate development.
- Support governance.
- Ensure consistency.
- Improve maintainability.
- Enable enterprise scalability.
- Support prompt composition.

---

# Scope

This library applies to:

- AI Assistants
- Digital Employees
- Enterprise Agents
- Copilots
- Workflow Automation
- Business Applications
- Multi-Agent Systems
- MCP Integrations
- Enterprise APIs

---

# Template Principles

## Principle 1 — Reuse First

New prompts SHALL reuse existing templates whenever possible.

---

## Principle 2 — Modular Design

Templates SHALL support modular composition.

---

## Principle 3 — Business Alignment

Templates SHALL reflect business objectives.

---

## Principle 4 — Technology Agnostic

Templates SHALL remain independent of individual LLM vendors.

---

## Principle 5 — Governed

Only approved templates SHALL be used in production.

---

## Principle 6 — Extensible

Templates SHALL support extension without modifying the base template.

---

# Enterprise Template Architecture

```text
Business Need
      │
      ▼
Template Selection
      │
      ▼
Template Composition
      │
      ▼
Variable Injection
      │
      ▼
Policy Injection
      │
      ▼
Knowledge Injection
      │
      ▼
Memory Injection
      │
      ▼
Runtime Context
      │
      ▼
Final Enterprise Prompt
```

---

# Template Structure

Every template SHALL contain:

- Template ID
- Template Name
- Description
- Category
- Business Purpose
- Owner
- Version
- Variables
- Constraints
- Dependencies
- Supported Models
- Output Contract
- Governance Rules

---

# Enterprise Template Categories

## System Templates

Reusable system instructions governing AI behaviour.

Examples:

- Enterprise Assistant
- Enterprise Reviewer
- Enterprise Planner
- Enterprise Architect

---

## Role Templates

Reusable persona definitions.

Examples:

- Product Manager
- UX Designer
- Enterprise Architect
- Legal Advisor
- HR Consultant
- Security Engineer

---

## Task Templates

Templates for standard business activities.

Examples:

- Analyse
- Summarise
- Explain
- Generate
- Review
- Optimise
- Compare
- Validate

---

## Workflow Templates

Templates supporting end-to-end processes.

Examples:

- Customer Onboarding
- Incident Response
- Change Management
- Software Delivery
- Product Discovery

---

## Decision Templates

Templates for:

- Risk Analysis
- Decision Evaluation
- Recommendation
- Prioritisation
- Trade-off Analysis

---

## Evaluation Templates

Templates supporting:

- Quality Review
- Compliance Validation
- Security Assessment
- Performance Evaluation
- Architecture Review

---

## Coding Templates

Templates supporting:

- Code Generation
- Refactoring
- Code Review
- Test Generation
- Documentation

---

## Knowledge Templates

Templates supporting:

- RAG
- Knowledge Search
- Citation Generation
- Knowledge Synthesis
- Research

---

## Agent Templates

Templates supporting:

- Agent Planning
- Agent Coordination
- Capability Discovery
- Delegation
- Collaboration

---

## Communication Templates

Templates supporting:

- Email
- Meeting Notes
- Reports
- Documentation
- Stakeholder Updates

---

# Standard Template Format

Every template SHALL contain:

```text
System Instructions

↓

Role Definition

↓

Business Objective

↓

Context

↓

Knowledge

↓

Memory

↓

User Request

↓

Constraints

↓

Output Format

↓

Validation Rules
```

---

# Template Variables

Templates SHALL support:

- Static Variables
- Dynamic Variables
- Environment Variables
- Business Variables
- User Variables
- Runtime Variables
- Memory Variables
- Knowledge Variables

---

# Variable Naming Convention

Variables SHALL use:

```text
{{variable_name}}
```

Examples:

```text
{{business_goal}}

{{user_name}}

{{company_name}}

{{knowledge}}

{{memory}}

{{runtime_context}}

{{output_schema}}
```

---

# Template Metadata

Each template SHALL include:

| Field | Description |
|---------|-------------|
| Template ID | Unique identifier |
| Version | Semantic version |
| Category | Template classification |
| Owner | Business owner |
| Technical Owner | Engineering owner |
| Status | Draft, Approved, Deprecated |
| Models | Supported LLMs |
| Risk Level | Low–Critical |

---

# Template Composition

Templates MAY inherit from:

- Base Templates
- Role Templates
- Capability Templates
- Domain Templates
- Workflow Templates

Composition SHALL support multiple inheritance.

---

# Template Registry

The Enterprise Template Registry SHALL maintain:

- Template Catalogue
- Dependencies
- Ownership
- Versions
- Usage Statistics
- Approval History
- Retirement Status

---

# Template Validation

Validation SHALL include:

- Schema Validation
- Variable Validation
- Dependency Validation
- Policy Validation
- Security Review
- Output Validation

---

# Template Governance

Templates SHALL include:

- Business Owner
- Technical Owner
- Approval Workflow
- Change History
- Review Schedule
- Compliance Mapping

---

# Template Metrics

Track:

- Reuse Rate
- Usage Frequency
- Success Rate
- Quality Score
- Average Tokens
- Response Time
- User Satisfaction
- Cost per Execution

---

# Naming Convention

Template IDs SHALL follow:

```text
TPL-{CATEGORY}-{NUMBER}
```

Example:

```text
TPL-SYSTEM-001

TPL-ROLE-004

TPL-WORKFLOW-018
```

---

# Versioning

Semantic Versioning SHALL be used.

Examples:

```text
1.0.0

1.2.0

2.0.0
```

---

# Governance

The Enterprise Prompt Template Library SHALL be governed by:

- Chief AI Architect
- Prompt Engineering Team
- Enterprise Architecture Board
- AI Governance Board

New templates SHALL undergo architecture and governance review before publication.

---

# Quality Gates

A template SHALL fail validation if:

- Required metadata is missing.
- Variables are undefined.
- Output contract is incomplete.
- Security review is absent.
- Governance approval is missing.
- Naming standards are violated.

---

# Deliverables

Mandatory artefacts include:

- Template Catalogue
- Template Definitions
- Variable Dictionary
- Registry Entries
- Validation Reports
- Governance Records
- Usage Analytics

---

# Success Metrics

Track:

- Template Reuse Rate
- Prompt Development Time Reduction
- Prompt Consistency
- Governance Compliance
- Quality Improvement
- Prompt Standardisation
- User Satisfaction
- Business Value Generated
- Cost Optimisation

---

# References

- PROMPT_ARCHITECTURE.md
- PROMPT_LIFECYCLE.md
- PROMPT_REGISTRY.md
- PROMPT_GOVERNANCE.md
- PROMPT_SECURITY.md
- PROMPT_OBSERVABILITY.md
- AI_OPERATING_MODEL.md
- QUALITY_GATES.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise AI Platform Architecture Office | Initial Enterprise Prompt Template Library |
