# Enterprise Prompt Variable Model

**Document ID:** AI-PROMPT-008

**Version:** 1.0.0

**Status:** APPROVED

**Owner:** Enterprise AI Platform Architecture Office

**Classification:** Enterprise Prompt Variable Standard

**Parent:** PROMPT_CONTEXT_MODEL.md

---

# Purpose

The Enterprise Prompt Variable Model defines the architecture, governance, lifecycle and resolution rules for variables used within Enterprise Prompts across the Enterprise AI Operating System (EAIOS).

Variables separate business logic from prompt implementation, enabling reusable, dynamic and context-aware prompt composition while maintaining governance, consistency and security.

Every enterprise prompt SHALL use governed variables instead of hard-coded values wherever practical.

---

# Objectives

The Enterprise Prompt Variable Model SHALL:

- Standardise variable definition.
- Enable reusable prompt templates.
- Support runtime composition.
- Improve maintainability.
- Reduce prompt duplication.
- Ensure deterministic resolution.
- Support enterprise governance.
- Enable model independence.
- Improve security.
- Optimise prompt execution.

---

# Scope

This standard applies to:

- Prompt Templates
- Prompt Modules
- Prompt Patterns
- Workflow Prompts
- Agent Prompts
- Enterprise Assistants
- Digital Employees
- MCP Servers
- AI APIs
- Multi-Agent Systems

---

# Variable Principles

## Principle 1 — Variables Represent Intent

Variables SHALL represent business concepts rather than implementation details.

---

## Principle 2 — Runtime Resolution

Variables SHALL be resolved during prompt composition.

---

## Principle 3 — Strong Typing

Every variable SHALL define its data type and validation rules.

---

## Principle 4 — Immutable During Execution

Resolved variables SHALL remain immutable throughout a single execution.

---

## Principle 5 — Governed Access

Variables SHALL respect enterprise security and access controls.

---

## Principle 6 — Complete Traceability

Every resolved variable SHALL be traceable to its originating source.

---

# Enterprise Variable Architecture

```text
Prompt Template
       │
       ▼
Variable Parser
       │
       ▼
Variable Registry
       │
       ▼
Variable Resolver
       │
       ▼
Context Engine
       │
       ▼
Knowledge Engine
       │
       ▼
Memory Engine
       │
       ▼
Policy Validation
       │
       ▼
Resolved Prompt
```

---

# Variable Categories

Enterprise variables SHALL be categorised as:

## Static Variables

Fixed organisational values.

Examples:

- Company Name
- Brand Identity
- Default Locale

---

## Runtime Variables

Generated during execution.

Examples:

- Current Time
- Session ID
- Execution ID
- Environment

---

## User Variables

User-specific values.

Examples:

- User Name
- Role
- Department
- Language
- Preferences

---

## Business Variables

Business-specific information.

Examples:

- Project Name
- Product
- Customer
- Business Goal
- Initiative

---

## Workflow Variables

Workflow state information.

Examples:

- Current Stage
- Task Owner
- Workflow ID
- Approval Status

---

## Knowledge Variables

Resolved from enterprise knowledge.

Examples:

- Retrieved Documents
- Policies
- Product Specifications
- SOP References

---

## Memory Variables

Resolved from memory services.

Examples:

- Previous Conversations
- User Preferences
- Historical Decisions
- Episodic Memory

---

## Agent Variables

Agent execution metadata.

Examples:

- Agent Name
- Capability
- Available Tools
- Confidence Score

---

## Environment Variables

Infrastructure information.

Examples:

- Region
- Tenant
- Deployment
- API Endpoint

---

# Variable Syntax

Enterprise variables SHALL use:

```text
{{variable_name}}
```

Examples:

```text
{{user.name}}

{{workflow.stage}}

{{memory.summary}}

{{knowledge.documents}}

{{business.goal}}

{{agent.capabilities}}

{{runtime.timestamp}}
```

---

# Variable Naming Convention

Variable names SHALL:

- Use lowercase.
- Use dot notation.
- Represent business meaning.
- Avoid implementation details.
- Remain vendor independent.

Examples:

```text
business.goal

user.role

memory.history

knowledge.references

workflow.status

runtime.locale
```

---

# Variable Types

Supported types:

- String
- Integer
- Decimal
- Boolean
- Date
- Time
- DateTime
- Enumeration
- Array
- Object
- JSON
- Markdown
- Reference

---

# Variable Resolution Order

Variables SHALL resolve in the following sequence:

1. Runtime Variables
2. User Variables
3. Workflow Variables
4. Business Variables
5. Agent Variables
6. Memory Variables
7. Knowledge Variables
8. Environment Variables
9. Default Values

---

# Variable Validation

Each variable SHALL define:

- Data Type
- Mandatory Status
- Allowed Values
- Validation Rules
- Default Value
- Null Behaviour
- Security Classification

---

# Variable Security

Variables SHALL support:

- Encryption
- Access Control
- Tenant Isolation
- Secret Masking
- Audit Logging
- Policy Enforcement
- Classification Labels

Sensitive variables SHALL NEVER be exposed directly to the LLM unless explicitly authorised.

---

# Variable Registry

The Enterprise Variable Registry SHALL maintain:

- Variable Catalogue
- Ownership
- Data Types
- Dependencies
- Validation Rules
- Usage Statistics
- Version History
- Security Classification

---

# Variable Lifecycle

Variables SHALL progress through:

1. Definition
2. Registration
3. Validation
4. Approval
5. Publication
6. Runtime Resolution
7. Monitoring
8. Deprecation
9. Retirement

---

# Variable Metadata

Every variable SHALL include:

- Variable ID
- Name
- Description
- Category
- Data Type
- Owner
- Version
- Default Value
- Source
- Classification
- Status

---

# Dependency Management

Variables MAY depend on:

- Other Variables
- Context Objects
- Knowledge Sources
- Memory Objects
- Runtime Services
- Workflow State

Circular dependencies SHALL be rejected.

---

# Variable Metrics

Track:

- Resolution Success Rate
- Resolution Time
- Missing Variables
- Default Value Usage
- Security Violations
- Reuse Rate
- Resolution Accuracy
- Variable Freshness
- Runtime Failures

---

# Governance

The Enterprise Prompt Variable Model SHALL be governed by:

- Chief AI Architect
- Prompt Engineering Team
- AI Governance Board
- Enterprise Architecture Board
- Platform Engineering

Variable definitions SHALL be reviewed quarterly.

---

# Quality Gates

Variable resolution SHALL fail if:

- Mandatory variables are missing.
- Validation rules fail.
- Variable source is unavailable.
- Circular dependencies exist.
- Security policies are violated.
- Variable type is invalid.
- Registry lookup fails.

---

# Deliverables

The Variable Model SHALL produce:

- Variable Catalogue
- Variable Registry
- Variable Dictionary
- Dependency Graph
- Resolution Report
- Validation Report
- Security Assessment
- Usage Analytics Dashboard

---

# Success Metrics

Track:

- Variable Reuse Rate
- Resolution Accuracy
- Prompt Maintainability
- Governance Compliance
- Runtime Reliability
- Token Optimisation
- Security Compliance
- Response Consistency
- Engineering Productivity

---

# References

- PROMPT_ARCHITECTURE.md
- PROMPT_COMPOSITION.md
- PROMPT_CONTEXT_MODEL.md
- PROMPT_VERSIONING.md
- PROMPT_REGISTRY.md
- MEMORY_ARCHITECTURE.md
- KNOWLEDGE_ARCHITECTURE.md
- QUALITY_GATES.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise AI Platform Architecture Office | Initial Enterprise Prompt Variable Model |
