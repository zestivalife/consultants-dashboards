# Enterprise Prompt Context Model

**Document ID:** AI-PROMPT-007

**Version:** 1.0.0

**Status:** APPROVED

**Owner:** Enterprise AI Platform Architecture Office

**Classification:** Enterprise Context Architecture Standard

**Parent:** PROMPT_COMPOSITION.md

---

# Purpose

The Enterprise Prompt Context Model defines how contextual information is discovered, classified, prioritised, assembled and injected into prompts across the Enterprise AI Operating System (EAIOS).

Context is the primary determinant of AI quality. A prompt without appropriate context is incomplete, regardless of its instructions.

The Context Model ensures that every prompt executes with the minimum necessary, maximum relevant and fully governed contextual information.

---

# Objectives

The Enterprise Prompt Context Model SHALL:

- Standardise contextual information.
- Improve response accuracy.
- Reduce hallucinations.
- Enable context reuse.
- Support adaptive AI behaviour.
- Minimise unnecessary token usage.
- Enable deterministic prompt execution.
- Improve governance.
- Support multi-agent collaboration.
- Preserve contextual traceability.

---

# Scope

This standard applies to:

- AI Assistants
- Enterprise Agents
- Digital Employees
- Workflow Engines
- Copilots
- MCP Servers
- Enterprise APIs
- RAG Systems
- Multi-Agent Systems

---

# Context Principles

## Principle 1 — Context Before Instructions

Relevant context SHALL always be resolved before prompt execution.

---

## Principle 2 — Minimum Sufficient Context

Only the information required to achieve the business objective SHALL be injected.

---

## Principle 3 — Dynamic Assembly

Context SHALL be assembled dynamically at runtime.

---

## Principle 4 — Governed Context

Every contextual source SHALL comply with enterprise governance policies.

---

## Principle 5 — Traceable Context

Every context item SHALL have provenance and version history.

---

## Principle 6 — Context Isolation

Tenant, organisation and security boundaries SHALL always be maintained.

---

# Enterprise Context Architecture

```text
User Request
      │
      ▼
Intent Detection
      │
      ▼
Context Discovery
      │
      ▼
Context Classification
      │
      ▼
Context Prioritisation
      │
      ▼
Context Assembly
      │
      ▼
Policy Filtering
      │
      ▼
Token Optimisation
      │
      ▼
Prompt Composition
      │
      ▼
LLM Execution
```

---

# Context Layers

Enterprise prompts SHALL assemble context from the following layers.

## Layer 1 — Enterprise Policies

Includes:

- Security Policies
- Privacy Rules
- Compliance Requirements
- Governance Standards
- Regulatory Controls

---

## Layer 2 — Business Context

Includes:

- Business Objectives
- Organisation
- Department
- Project
- Programme
- Product
- Customer

---

## Layer 3 — Workflow Context

Includes:

- Current Workflow
- Active Stage
- Pending Tasks
- Dependencies
- Milestones

---

## Layer 4 — User Context

Includes:

- Role
- Permissions
- Preferences
- Language
- Time Zone
- Experience Level

---

## Layer 5 — Knowledge Context

Includes:

- Retrieved Documents
- Product Documentation
- SOPs
- Policies
- Knowledge Graph
- Domain References

---

## Layer 6 — Memory Context

Includes:

- Long-Term Memory
- Working Memory
- Conversation Memory
- Session Memory
- Episodic Memory

---

## Layer 7 — Runtime Context

Includes:

- Environment
- Active Services
- Connected Tools
- Available Agents
- Model
- Runtime Variables

---

## Layer 8 — Interaction Context

Includes:

- Current Conversation
- Previous Requests
- Attachments
- Uploaded Files
- User Corrections

---

# Context Sources

Supported sources include:

- Enterprise Knowledge Base
- Product Documentation
- Memory Services
- Workflow Engine
- Identity Platform
- Policy Engine
- MCP Servers
- External APIs
- User Session
- Agent Registry

---

# Context Classification

Context SHALL be classified as:

- Mandatory
- Required
- Optional
- Supplemental
- Historical
- Informational
- Restricted
- Confidential

---

# Context Priority

Priority SHALL be applied in the following order:

1. Enterprise Policies
2. Security Requirements
3. Business Objectives
4. Active Workflow
5. Current User Request
6. Knowledge Retrieval
7. Memory
8. Historical Context
9. Supplemental Context

---

# Context Resolution Pipeline

```text
Discover
    │
    ▼
Collect
    │
    ▼
Validate
    │
    ▼
Deduplicate
    │
    ▼
Rank
    │
    ▼
Filter
    │
    ▼
Compress
    │
    ▼
Inject
```

---

# Context Validation

Every context item SHALL be validated for:

- Source Authenticity
- Version
- Freshness
- Ownership
- Access Rights
- Security Classification
- Data Integrity

---

# Context Optimisation

Optimisation SHALL include:

- Duplicate Removal
- Semantic Compression
- Relevance Ranking
- Token Budget Management
- Noise Elimination
- Context Summarisation

---

# Context Window Allocation

The Prompt Composition Engine SHALL allocate context windows dynamically according to:

| Context Type | Priority |
|--------------|----------|
| Policies | Critical |
| Business Objectives | Critical |
| Workflow | High |
| User Context | High |
| Knowledge | High |
| Memory | Medium |
| Historical | Low |
| Supplemental | Lowest |

---

# Context Metadata

Every context object SHALL contain:

- Context ID
- Source
- Owner
- Classification
- Version
- Timestamp
- Security Level
- Priority
- Token Size
- Expiration Policy

---

# Context Registry

The Enterprise Context Registry SHALL maintain:

- Context Catalogue
- Source Registry
- Classification
- Priority Matrix
- Dependency Graph
- Version History
- Usage Analytics

---

# Context Metrics

Track:

- Context Coverage
- Context Relevance
- Token Utilisation
- Retrieval Accuracy
- Freshness
- Redundancy
- Compression Ratio
- Response Quality Impact
- Hallucination Reduction

---

# Governance

The Enterprise Prompt Context Model SHALL be governed by:

- Chief AI Architect
- AI Governance Board
- Enterprise Architecture Board
- Prompt Engineering Team
- Knowledge Management Team

Context policies SHALL be reviewed quarterly.

---

# Quality Gates

Context injection SHALL fail if:

- Mandatory context is unavailable.
- Security validation fails.
- Context ownership is unknown.
- Policies cannot be resolved.
- Context exceeds approved limits.
- Version conflicts exist.
- Required knowledge is unavailable.

---

# Deliverables

The Context Model SHALL produce:

- Context Manifest
- Context Registry
- Context Dependency Graph
- Context Classification Matrix
- Context Resolution Report
- Context Validation Report
- Context Analytics Dashboard

---

# Success Metrics

Track:

- Context Accuracy
- Context Completeness
- Context Freshness
- Retrieval Precision
- Hallucination Reduction
- Token Efficiency
- Governance Compliance
- Business Outcome Achievement
- Response Quality Improvement

---

# References

- PROMPT_ARCHITECTURE.md
- PROMPT_COMPOSITION.md
- MEMORY_ARCHITECTURE.md
- KNOWLEDGE_ARCHITECTURE.md
- RAG_ARCHITECTURE.md
- AI_OPERATING_MODEL.md
- QUALITY_GATES.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise AI Platform Architecture Office | Initial Enterprise Prompt Context Model |
