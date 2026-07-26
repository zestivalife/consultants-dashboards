# AI Context Engine

**Document ID:** AI-GOV-003  
**Version:** 1.0.0  
**Status:** APPROVED  
**Owner:** Enterprise Architecture Office  
**Classification:** Internal  
**Parent Document:** AI_OPERATING_MODEL.md

---

# Purpose

The AI Context Engine defines how AI systems discover, prioritise, validate and consume repository knowledge before performing any engineering activity.

It prevents incomplete reasoning by ensuring AI acquires the appropriate architectural, business and technical context before analysis, planning or implementation.

The Context Engine is responsible for **knowledge acquisition**, not engineering reasoning.

---

# Mission

Ensure every engineering decision is based on the most relevant, authoritative and up-to-date repository knowledge.

---

# Vision

Enable AI to navigate the repository with the discipline of an experienced engineer who understands where information lives, how it relates to other artefacts, and which sources should be trusted.

---

# Objectives

The AI Context Engine aims to:

- Minimise missing context.
- Reduce unnecessary context loading.
- Identify authoritative documentation.
- Detect conflicting information.
- Build repository awareness.
- Improve engineering accuracy.
- Optimise AI context usage.
- Support scalable repositories.

---

# Scope

The Context Engine governs:

- Repository discovery
- Knowledge acquisition
- Context prioritisation
- Source-of-Truth resolution
- Dependency discovery
- Cross-reference validation
- Repository traversal
- Context optimisation

It does not perform engineering reasoning or implementation.

---

# Repository Intelligence Model

The repository should be understood as a connected knowledge graph rather than a collection of independent files.

```
Repository

↓

Governance

↓

Architecture

↓

Platform

↓

Domains

↓

Products

↓

Applications

↓

Services

↓

APIs

↓

Events

↓

Data Models

↓

Infrastructure

↓

Implementation

↓

Testing

↓

Operations
```

Context should be acquired by traversing this graph instead of randomly opening documents.

---

# Context Acquisition Lifecycle

Every request shall follow the same discovery lifecycle.

```
Receive Request
        │
        ▼
Classify Request
        │
        ▼
Identify Capability
        │
        ▼
Identify Repository Areas
        │
        ▼
Locate Sources of Truth
        │
        ▼
Discover Dependencies
        │
        ▼
Build Context Graph
        │
        ▼
Validate Context
        │
        ▼
Pass Context to Cognitive Engine
```

---

# Request Classification

Every request should first be classified.

Examples include:

- Architecture
- Platform
- Shared Service
- Microservice
- Product
- Feature
- Documentation
- API
- Database
- Security
- Infrastructure
- Testing
- Operations

Classification determines the context loading strategy.

---

# Context Categories

Context is organised into four categories.

## Mandatory Context

Always required.

Examples:

- AGENTS.md
- MASTER_ARCHITECT.md
- AI Operating Model
- Repository Governance

---

## Required Context

Specific to the current task.

Examples:

- Platform documentation
- Service specifications
- Product specifications
- API contracts
- Database models

---

## Supporting Context

Useful for improving recommendations.

Examples:

- ADRs
- Milestones
- Design decisions
- Previous implementations
- Standards

---

## Discovery Context

Loaded only when necessary.

Examples:

- Source code
- Test suites
- Deployment manifests
- Infrastructure
- Historical documentation

---

# Context Priority Model

When multiple documents describe the same concept, higher authority prevails.

```
Repository Governance
        │
        ▼
Enterprise Architecture
        │
        ▼
Platform Specifications
        │
        ▼
Shared Services
        │
        ▼
Business Domains
        │
        ▼
Products
        │
        ▼
Applications
        │
        ▼
Milestones
        │
        ▼
Implementation
        │
        ▼
Tests
```

Implementation should never redefine architecture.

---

# Repository Traversal Strategy

Traversal should follow repository ownership.

```
Capability

↓

Domain

↓

Product

↓

Service

↓

API

↓

Data

↓

Implementation

↓

Tests
```

Traversal should stop when sufficient authoritative knowledge has been acquired.

---

# Context Loading Strategy

Load context progressively.

```
Mandatory

↓

Required

↓

Supporting

↓

Discovery
```

Avoid loading unrelated repository areas.

---

# Search Strategies

## Architecture Search

Load:

- Enterprise Architecture
- Platform
- Governance

---

## Product Search

Load:

- Product
- Domain
- Platform

---

## Service Search

Load:

- Service
- API
- Database
- Events

---

## Frontend Search

Load:

- Product
- UX
- Design System
- APIs

---

## Mobile Search

Load:

- Product
- Mobile Specifications
- APIs
- Notifications

---

## Infrastructure Search

Load:

- Infrastructure
- Deployment
- DevOps
- Security

---

## Documentation Search

Load:

- Related specifications
- Standards
- Templates
- ADRs

---

# Dependency Discovery

Before execution AI should identify:

Upstream Dependencies

- Platform
- Shared Services
- External APIs
- Infrastructure

Current Scope

Downstream Dependencies

- Products
- Consumers
- Documentation
- Tests
- Deployment

---

# Repository Knowledge Graph

The Context Engine should construct a temporary knowledge graph for each request.

Relationships include:

- Capability → Domain
- Domain → Product
- Product → Service
- Service → API
- API → Events
- API → Database
- Service → Infrastructure
- Product → Mobile
- Product → Web
- Service → Tests
- Service → Documentation

The graph exists only for the duration of the request.

---

# Source of Truth Resolution

When multiple artefacts exist:

1. Prefer approved governance documents.
2. Prefer architecture over implementation.
3. Prefer platform specifications over product-specific documentation.
4. Prefer current implementation over obsolete documentation when governance permits.
5. Escalate unresolved conflicts.

Never merge conflicting information without validation.

---

# Freshness Rules

Prefer:

- Approved documents
- Current implementation
- Latest architectural decisions
- Active milestones

Ignore:

- Deprecated documents
- Archived specifications
- Superseded ADRs
- Obsolete implementations

---

# Context Budget

AI should optimise context usage.

Priority order:

1. Mandatory
2. Required
3. Supporting
4. Discovery

Load only the minimum context necessary to produce a high-confidence response.

---

# Conflict Detection

The Context Engine should identify:

- Duplicate specifications
- Duplicate APIs
- Conflicting terminology
- Conflicting ownership
- Missing documentation
- Broken references
- Circular dependencies

Conflicts should be surfaced before reasoning begins.

---

# Cross-Reference Validation

Verify:

- Parent-child relationships
- Internal document references
- Service ownership
- Platform ownership
- Domain ownership
- API ownership

Broken references should be reported.

---

# Completion Criteria

Context acquisition is complete when:

✓ Repository area identified

✓ Capability identified

✓ Source of Truth established

✓ Dependencies identified

✓ Required documents loaded

✓ Context confidence is acceptable

Only then may the Cognitive Engine begin engineering reasoning.

---

# Relationships

## Parent

- AI_OPERATING_MODEL.md

## Consumed By

- AI_COGNITIVE_ENGINE.md
- AI_DECISION_FRAMEWORK.md
- All AI Roles
- All AI Workflows

## Supports

- Repository Intelligence
- Knowledge Discovery
- Dependency Analysis

---

# Success Criteria

The AI Context Engine is successful when:

- AI consistently uses authoritative repository knowledge.
- Unnecessary context loading is minimised.
- Repository conflicts are detected early.
- Source-of-Truth violations are prevented.
- Engineering accuracy improves.
- Large repositories remain navigable and maintainable.

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise Architecture Office | Initial AI Context Engine specification |
