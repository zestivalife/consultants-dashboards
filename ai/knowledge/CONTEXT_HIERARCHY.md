# Enterprise Context Hierarchy

**Document ID:** AI-KA-005
**Version:** 1.0.0
**Status:** APPROVED
**Owner:** Knowledge Architecture Office
**Classification:** Enterprise Standard
**Parent:** KNOWLEDGE_ARCHITECTURE.md

---

# Purpose

The Enterprise Context Hierarchy defines how contextual information SHALL be selected, prioritised, assembled, governed and delivered to AI systems operating within the Enterprise AI Operating System (EAIOS).

Rather than exposing the entire knowledge repository to every AI interaction, this standard ensures that only the most relevant, authoritative and contextual information is retrieved for reasoning.

The Context Hierarchy provides the foundation for:

- Retrieval-Augmented Generation (RAG)
- AI Memory
- Multi-Agent Collaboration
- Context Engineering
- AI Decision Intelligence
- Autonomous Planning
- Enterprise AI Governance

Every AI interaction SHALL be governed by this hierarchy.

---

# Objectives

The Enterprise Context Hierarchy SHALL:

- Deliver relevant context.
- Minimise irrelevant information.
- Reduce hallucinations.
- Improve reasoning quality.
- Support multi-agent collaboration.
- Enable deterministic context selection.
- Improve response consistency.
- Support token optimisation.
- Improve explainability.
- Maintain enterprise governance.

---

# Scope

This hierarchy applies to:

- AI Agents
- Prompt Assembly
- RAG Pipelines
- AI Memory
- Knowledge Graph Traversal
- Workflow Execution
- Decision Support
- Code Generation
- Documentation Generation
- Enterprise Search

All AI reasoning SHALL use governed context.

---

# Context Principles

## Principle 1 — Context Before Generation

AI SHALL assemble context before generating any output.

---

## Principle 2 — Minimum Sufficient Context

Only the minimum context required to complete the task SHALL be provided.

---

## Principle 3 — Trust Before Relevance

Authoritative knowledge SHALL always take precedence over highly similar but less trusted information.

---

## Principle 4 — Freshness Matters

When multiple valid assets exist, the most recently approved version SHALL be preferred.

---

## Principle 5 — Security First

Context SHALL respect enterprise security classifications and access controls.

---

## Principle 6 — Explainability

Every context element SHALL be traceable to its originating knowledge asset.

---

# Context Hierarchy

Context SHALL be assembled using the following priority order:

```
Level 1

System Instructions

↓

Level 2

Enterprise Governance

↓

Level 3

Knowledge Architecture

↓

Level 4

Domain Knowledge

↓

Level 5

Product Knowledge

↓

Level 6

Project Knowledge

↓

Level 7

Task Context

↓

Level 8

Conversation Context

↓

Level 9

Working Memory

↓

Level 10

User Input
```

Higher levels SHALL override lower levels when conflicts occur.

---

# Context Layers

## Layer 1 — System Context

Contains:

- AI Operating Model
- Enterprise Rules
- Safety Policies
- Core Behaviour

Immutable during execution.

---

## Layer 2 — Governance Context

Contains:

- Standards
- Policies
- Compliance Rules
- Architecture Principles

Governance SHALL override implementation guidance.

---

## Layer 3 — Architectural Context

Contains:

- Enterprise Architecture
- Solution Architecture
- Domain Architecture
- Design Principles

Provides structural reasoning.

---

## Layer 4 — Domain Context

Contains:

- Domain Models
- Business Rules
- Domain Standards
- Domain Vocabulary

Supports domain-specific intelligence.

---

## Layer 5 — Product Context

Contains:

- Product Vision
- PRDs
- Roadmaps
- Features
- User Stories

Supports product-aware reasoning.

---

## Layer 6 — Project Context

Contains:

- Sprint Plans
- Tasks
- Milestones
- ADRs
- Release Plans

Supports execution.

---

## Layer 7 — Task Context

Contains:

- Current Objective
- Inputs
- Constraints
- Deliverables
- Acceptance Criteria

Task context SHALL be regenerated for every execution.

---

## Layer 8 — Conversation Context

Contains:

- Previous Messages
- Clarifications
- User Decisions

Conversation context SHALL be transient.

---

## Layer 9 — Working Memory

Contains:

- Intermediate Decisions
- Temporary Variables
- Execution State

Working memory SHALL exist only during execution.

---

## Layer 10 — User Context

Contains:

- Current Prompt
- Attachments
- Inputs
- Parameters

User context SHALL never override enterprise governance.

---

# Context Assembly Pipeline

```
User Request
      │
      ▼
Intent Detection
      │
      ▼
Knowledge Retrieval
      │
      ▼
Knowledge Graph Expansion
      │
      ▼
Context Ranking
      │
      ▼
Context Deduplication
      │
      ▼
Conflict Resolution
      │
      ▼
Token Optimisation
      │
      ▼
Prompt Assembly
      │
      ▼
AI Reasoning
```

---

# Context Selection Rules

Context SHALL be selected using:

- Authority
- Relevance
- Freshness
- Completeness
- Security Classification
- Semantic Similarity
- Knowledge Relationships
- User Intent
- Task Requirements

---

# Context Conflict Resolution

Conflicts SHALL be resolved using the following order:

1. Enterprise Governance
2. Approved Standards
3. Architecture Documents
4. Product Specifications
5. Project Documentation
6. Working Memory
7. User Conversation

Lower-priority context SHALL NOT override higher-priority knowledge.

---

# Context Window Management

The Context Engine SHALL:

- Remove duplicates.
- Eliminate obsolete assets.
- Merge related information.
- Prioritise canonical sources.
- Optimise token usage.
- Preserve reasoning continuity.

---

# Multi-Agent Context

Each AI Agent SHALL receive:

- Shared Enterprise Context
- Shared Product Context
- Agent-Specific Context
- Task-Specific Context
- Temporary Working Memory

Agents SHALL exchange knowledge through governed context rather than unrestricted conversation.

---

# Context Traceability

Every AI response SHALL identify:

- Context Sources
- Knowledge IDs
- Document Versions
- Confidence Score

Responses SHALL remain fully auditable.

---

# Governance

The Context Hierarchy SHALL be governed by:

- Knowledge Architect
- AI Platform Architect
- Enterprise Architect
- Product Architect
- Domain Architects

Changes SHALL require governance approval.

---

# Quality Gates

Context assembly SHALL fail if:

- Mandatory governance documents are missing.
- Context exceeds token limits without optimisation.
- Duplicate canonical sources exist.
- Security violations are detected.
- Required product context is unavailable.
- Context traceability cannot be established.

---

# Deliverables

Mandatory artefacts include:

- Context Hierarchy Model
- Context Assembly Rules
- Context Ranking Matrix
- Context Conflict Matrix
- Context Source Registry
- Context Validation Report

---

# Success Metrics

Track:

- Context Precision
- Context Recall
- Token Efficiency
- Response Accuracy
- Hallucination Rate
- Context Freshness
- Retrieval Latency
- Traceability Coverage
- Context Reuse Rate

---

# References

- KNOWLEDGE_ARCHITECTURE.md
- KNOWLEDGE_TAXONOMY.md
- KNOWLEDGE_GRAPH.md
- DOCUMENT_CLASSIFICATION.md
- RAG_ARCHITECTURE.md *(Future)*
- MEMORY_MODEL.md *(Future)*

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Knowledge Architecture Office | Initial Enterprise Context Hierarchy |
