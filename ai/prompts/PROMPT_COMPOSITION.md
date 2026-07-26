# Enterprise Prompt Composition Standard

**Document ID:** AI-PROMPT-006

**Version:** 1.0.0

**Status:** APPROVED

**Owner:** Enterprise AI Platform Architecture Office

**Classification:** Enterprise Prompt Composition Standard

**Parent:** PROMPT_ARCHITECTURE.md

---

# Purpose

The Enterprise Prompt Composition Standard defines how enterprise prompts are dynamically assembled from reusable components, policies, contextual information, organisational knowledge, memory, agent capabilities and runtime metadata.

Rather than storing large monolithic prompts, the Enterprise AI Operating System (EAIOS) SHALL generate prompts dynamically through a governed Prompt Composition Engine.

Prompt Composition transforms prompts from static text into executable enterprise artefacts.

---

# Objectives

The Enterprise Prompt Composition Standard SHALL:

- Enable modular prompt construction.
- Improve prompt reuse.
- Reduce duplication.
- Standardise composition logic.
- Support dynamic context injection.
- Improve governance.
- Enable multi-model optimisation.
- Support enterprise scalability.
- Improve maintainability.
- Ensure deterministic prompt assembly.

---

# Scope

This standard applies to:

- AI Assistants
- Enterprise Agents
- Digital Employees
- Workflow Engines
- Copilots
- API Services
- Multi-Agent Systems
- MCP Servers
- RAG Pipelines

---

# Composition Principles

## Principle 1 — Modular Assembly

Every prompt SHALL be assembled from reusable prompt modules.

---

## Principle 2 — Separation of Concerns

Prompt logic SHALL be separated into independent composition layers.

---

## Principle 3 — Context First

Runtime context SHALL be injected before execution.

---

## Principle 4 — Governance by Default

Policies SHALL automatically become part of every composed prompt.

---

## Principle 5 — Adaptive Composition

Composition SHALL adapt to:

- User intent
- Agent capability
- Business objective
- Selected model
- Runtime environment

---

## Principle 6 — Deterministic Execution

Identical inputs SHALL produce identical composed prompts.

---

# Enterprise Composition Architecture

```text
Business Goal
      │
      ▼
Prompt Template
      │
      ▼
Role Module
      │
      ▼
Capability Module
      │
      ▼
Policy Module
      │
      ▼
Knowledge Module
      │
      ▼
Memory Module
      │
      ▼
Runtime Context
      │
      ▼
User Request
      │
      ▼
Output Contract
      │
      ▼
Validation Rules
      │
      ▼
Final Enterprise Prompt
```

---

# Composition Layers

Every composed prompt SHALL include the following layers in sequence:

## Layer 1 — Enterprise Policies

Defines:

- Security policies
- Compliance requirements
- Data governance
- Privacy rules
- Enterprise standards

---

## Layer 2 — Role Definition

Defines:

- Persona
- Behaviour
- Authority
- Communication style
- Decision boundaries

---

## Layer 3 — Business Objective

Defines:

- Purpose
- Desired outcome
- Success criteria
- KPIs

---

## Layer 4 — Capability Layer

Declares:

- Tools
- APIs
- MCP Servers
- Available skills
- Execution permissions

---

## Layer 5 — Knowledge Layer

Injects:

- RAG documents
- Enterprise knowledge
- Domain references
- Product documentation

---

## Layer 6 — Memory Layer

Injects:

- Long-term memory
- Session memory
- User preferences
- Historical interactions

---

## Layer 7 — Runtime Context

Includes:

- Current workflow
- Active task
- Environment
- Time
- Locale
- Tenant
- Organisation

---

## Layer 8 — User Input

Contains:

- Request
- Attachments
- Variables
- Parameters

---

## Layer 9 — Output Contract

Defines:

- Response format
- JSON schema
- Markdown structure
- Validation requirements

---

## Layer 10 — Validation Rules

Defines:

- Output validation
- Security checks
- Policy compliance
- Quality expectations

---

# Composition Pipeline

```text
Template
    │
    ▼
Module Resolution
    │
    ▼
Dependency Resolution
    │
    ▼
Variable Expansion
    │
    ▼
Context Injection
    │
    ▼
Knowledge Injection
    │
    ▼
Memory Injection
    │
    ▼
Policy Injection
    │
    ▼
Validation
    │
    ▼
Execution Prompt
```

---

# Prompt Modules

Supported module types:

- Base Module
- Role Module
- Workflow Module
- Capability Module
- Knowledge Module
- Memory Module
- Security Module
- Governance Module
- Output Module
- Validation Module

---

# Variable Resolution

Variables SHALL resolve in the following priority:

1. Runtime Variables
2. User Variables
3. Workflow Variables
4. Business Variables
5. Memory Variables
6. Knowledge Variables
7. Environment Variables
8. Default Values

---

# Dependency Resolution

The Composition Engine SHALL validate:

- Module dependencies
- Capability dependencies
- Template inheritance
- Version compatibility
- Policy compatibility

Composition SHALL fail if mandatory dependencies cannot be resolved.

---

# Conflict Resolution

Where multiple modules define conflicting instructions, precedence SHALL be:

1. Enterprise Policies
2. Security Policies
3. Governance Policies
4. Business Objectives
5. Workflow Rules
6. Role Instructions
7. User Input
8. Default Template

---

# Composition Metadata

Every composed prompt SHALL include:

- Composition ID
- Prompt ID
- Template Version
- Module Versions
- Knowledge Snapshot
- Memory Snapshot
- Policy Version
- Model Target
- Timestamp

---

# Composition Registry

The Enterprise Prompt Composition Registry SHALL maintain:

- Composition Templates
- Module Catalogue
- Dependency Graph
- Variable Dictionary
- Composition History
- Execution Analytics

---

# Composition Metrics

Track:

- Composition Time
- Module Reuse Rate
- Variable Resolution Time
- Token Count
- Prompt Size
- Context Size
- Knowledge Coverage
- Memory Utilisation
- Composition Success Rate

---

# Governance

The Enterprise Prompt Composition Standard SHALL be governed by:

- Chief AI Architect
- Prompt Engineering Team
- AI Governance Board
- Enterprise Architecture Board

Composition rules SHALL be reviewed quarterly.

---

# Quality Gates

Prompt composition SHALL fail if:

- Required modules are missing.
- Mandatory policies are absent.
- Variable resolution fails.
- Dependencies are unresolved.
- Output contract is undefined.
- Security validation fails.
- Governance policies are violated.

---

# Deliverables

The composition process SHALL generate:

- Composed Prompt
- Composition Manifest
- Dependency Graph
- Variable Resolution Report
- Policy Injection Report
- Validation Report
- Execution Metadata

---

# Success Metrics

Track:

- Prompt Reuse
- Composition Accuracy
- Governance Compliance
- Module Reuse
- Response Quality
- Token Efficiency
- Execution Consistency
- Business Outcome Achievement
- Engineering Productivity

---

# References

- PROMPT_ARCHITECTURE.md
- PROMPT_TEMPLATE_LIBRARY.md
- PROMPT_PATTERN_CATALOG.md
- PROMPT_VERSIONING.md
- PROMPT_REGISTRY.md
- PROMPT_GOVERNANCE.md
- AI_OPERATING_MODEL.md
- QUALITY_GATES.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise AI Platform Architecture Office | Initial Enterprise Prompt Composition Standard |
