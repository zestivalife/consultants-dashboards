# AI Reasoning Patterns

**Document ID:** AI-GOV-005  
**Version:** 1.0.0  
**Status:** APPROVED  
**Owner:** Enterprise Architecture Office  
**Classification:** Internal  
**Parent Document:** AI_DECISION_FRAMEWORK.md

---

# Purpose

The AI Reasoning Patterns define structured approaches for different categories of engineering work.

Each pattern provides a repeatable reasoning strategy that enables AI to analyse problems consistently while adapting its approach to the nature of the task.

Reasoning patterns guide *how a request should be analysed*, not how it should be implemented.

---

# Mission

Provide specialised reasoning strategies that improve engineering quality, reduce inconsistency and ensure every request is approached using the most appropriate analytical model.

---

# Vision

Enable AI to select the most effective engineering reasoning strategy based on the request rather than applying the same thought process to every task.

---

# Objectives

The Reasoning Patterns aim to:

- Standardise analytical approaches.
- Improve solution quality.
- Reduce reasoning errors.
- Promote architectural consistency.
- Enable specialised engineering behaviour.
- Improve explainability.

---

# Pattern Selection Lifecycle

Every request shall follow the same selection process.

```
Request
        │
        ▼
Classification
        │
        ▼
Pattern Selection
        │
        ▼
Context Acquisition
        │
        ▼
Cognitive Analysis
        │
        ▼
Decision Framework
        │
        ▼
Execution
```

Only one pattern should be primary.

Additional patterns may be used where appropriate.

---

# Pattern Catalogue

## Greenfield Product Design

Use when:

- Building a new product
- New platform
- New domain

Focus:

- Business capability
- Domain boundaries
- Platform architecture
- Scalability
- Extensibility

Deliverables:

- High-level architecture
- Capability map
- Roadmap
- Risks

---

## Existing Feature Enhancement

Use when:

- Adding functionality
- Improving workflows
- Extending modules

Focus:

- Existing architecture
- Backward compatibility
- Reuse
- User impact

Deliverables:

- Gap analysis
- Proposed changes
- Dependency assessment

---

## Bug Investigation

Use when:

- Functional defects
- Unexpected behaviour
- Production incidents

Focus:

- Root cause
- Reproduction
- Impact
- Resolution

Deliverables:

- Root cause analysis
- Fix recommendation
- Regression risks

---

## Architecture Review

Use when:

- Reviewing designs
- Assessing technical debt
- Validating architecture

Focus:

- Layering
- Dependencies
- Standards
- Maintainability

Deliverables:

- Findings
- Risks
- Recommendations

---

## API Design

Use when:

- Creating APIs
- Modifying contracts
- Versioning

Focus:

- Contracts
- Idempotency
- Validation
- Error handling
- Security

Deliverables:

- API specification
- Contract review
- Compatibility assessment

---

## Database Evolution

Use when:

- Schema changes
- New entities
- Migration

Focus:

- Normalisation
- Relationships
- Constraints
- Migration strategy

Deliverables:

- Data model
- Migration plan
- Risk assessment

---

## Performance Optimisation

Use when:

- Slow systems
- Scaling issues
- Bottlenecks

Focus:

- Measurement
- Profiling
- Optimisation
- Validation

Deliverables:

- Bottleneck analysis
- Optimisation plan
- Success metrics

---

## Security Assessment

Use when:

- Authentication
- Authorisation
- Data protection
- Compliance

Focus:

- Threat modelling
- Attack surface
- Least privilege
- Auditability

Deliverables:

- Security findings
- Mitigation plan
- Residual risks

---

## Refactoring

Use when:

- Improving code quality
- Reducing technical debt
- Simplifying architecture

Focus:

- Maintainability
- Readability
- Reuse
- Testability

Deliverables:

- Refactoring strategy
- Risk analysis
- Migration plan

---

## Documentation Engineering

Use when:

- Creating documentation
- Updating specifications
- Governance work

Focus:

- Accuracy
- Consistency
- Cross-references
- Source of Truth

Deliverables:

- Updated documentation
- Reference validation
- Change log

---

# Pattern Selection Rules

Pattern selection should consider:

- Request intent
- Business objective
- Repository context
- Impact scope
- Engineering discipline

If multiple patterns apply, nominate one Primary Pattern and one or more Supporting Patterns.

---

# Pattern Composition

Complex work may combine patterns.

Example:

```
Primary:
Greenfield Product Design

Supporting:
API Design
Database Evolution
Security Assessment
Documentation Engineering
```

The Primary Pattern governs the analytical approach.

---

# Pattern Constraints

Patterns must:

- Follow the AI Operating Model.
- Use the Context Engine.
- Apply the Cognitive Engine.
- Follow the Decision Framework.

Patterns must not redefine governance.

---

# Pattern Evolution

New patterns should be introduced when:

- A recurring engineering scenario emerges.
- Existing patterns become overly broad.
- New disciplines are adopted.

Existing patterns should evolve rather than duplicate functionality.

---

# Success Criteria

The Reasoning Patterns are successful when:

- Similar requests are analysed consistently.
- Engineering quality improves.
- Architecture remains coherent.
- AI selects appropriate analytical strategies.
- New patterns can be introduced without affecting existing governance.

---

# Relationships

## Parent

- AI_DECISION_FRAMEWORK.md

## Consumed By

- AI_EXECUTION_ENGINE.md
- AI_COLLABORATION_MODEL.md
- All AI Roles
- All AI Workflows

## Supports

- Engineering Analysis
- Solution Design
- Architecture Reviews
- Technical Planning

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise Architecture Office | Initial AI Reasoning Patterns specification |
