# Build Microservice Workflow

**Workflow ID:** AI-WF-004
**Version:** 1.0.0
**Status:** APPROVED
**Owner:** Enterprise Architecture Office
**Classification:** Internal
**Parent:** BUILD_FEATURE.md

---

# Purpose

This workflow defines the enterprise standard for designing, implementing, validating, deploying and operating microservices.

Each microservice SHALL represent a single business capability with clearly defined ownership, contracts, data boundaries and operational characteristics.

No microservice SHALL be implemented without following this workflow.

---

# Objectives

- Promote Domain-Driven Design.
- Ensure loose coupling.
- Encourage high cohesion.
- Enable independent deployment.
- Improve scalability.
- Standardise observability.
- Simplify maintenance.
- Reduce operational risk.

---

# Trigger Conditions

Execute this workflow when:

- A new business capability requires its own service.
- A monolith is decomposed.
- A bounded context is identified.
- A reusable platform capability is created.
- A legacy service requires replacement.

---

# Required Inputs

The workflow SHALL NOT begin until the following artefacts are available:

- Approved Feature Request
- Product Requirements Document (PRD)
- Architecture Decision Record (ADR)
- Domain Model
- Business Capability Definition
- Integration Requirements
- Non-functional Requirements
- Security Requirements

---

# Microservice Principles

Every microservice SHALL:

- Own one business capability.
- Own its own data.
- Expose well-defined contracts.
- Be independently deployable.
- Be independently testable.
- Be observable.
- Be resilient.
- Be secure by default.
- Avoid direct database sharing.

---

# Microservice Lifecycle

```
Business Capability
        │
        ▼
Domain Design
        │
        ▼
Service Design
        │
        ▼
API & Event Contracts
        │
        ▼
Security Review
        │
        ▼
Implementation
        │
        ▼
Testing
        │
        ▼
Documentation
        │
        ▼
Deployment
        │
        ▼
Monitoring
```

---

# Workflow Stages

## Stage 1 — Capability Identification

Owner: Product Architect

Activities:

- Define business capability.
- Validate business value.
- Identify stakeholders.
- Define success metrics.
- Determine service ownership.

Output:

Approved Business Capability.

---

## Stage 2 — Domain Design

Owner: Domain Architect

Activities:

- Define bounded context.
- Identify aggregates.
- Define entities.
- Define value objects.
- Identify domain events.
- Establish ownership.

Output:

Approved Domain Model.

---

## Stage 3 — Service Architecture

Owner: Solution Architect

Activities:

- Define service boundaries.
- Select communication style.
- Identify dependencies.
- Define resilience strategy.
- Review scalability.
- Assess failure scenarios.

Output:

Service Architecture.

---

## Stage 4 — API & Event Design

Owner: API Architect

Activities:

- Define REST/gRPC/GraphQL interfaces.
- Define event schemas.
- Define contracts.
- Version interfaces.
- Ensure backward compatibility.

Output:

Service Contract.

---

## Stage 5 — Data Architecture

Owner: Database Architect

Activities:

- Define service-owned database.
- Design schema.
- Review indexing.
- Define consistency model.
- Review retention policies.

Output:

Database Approval.

---

## Stage 6 — Security Review

Owner: Security Architect

Activities:

- Authentication.
- Authorisation.
- Secrets management.
- Encryption.
- Threat modelling.
- Compliance validation.

Output:

Security Approval.

---

## Stage 7 — Implementation

Owner: Backend Architect

Activities:

- Implement business logic.
- Implement APIs.
- Publish events.
- Consume events.
- Add structured logging.
- Implement health checks.
- Implement metrics.

Output:

Working Microservice.

---

## Stage 8 — Quality Engineering

Owner: QA Architect

Activities:

- Unit testing.
- Integration testing.
- Contract testing.
- Event testing.
- Performance testing.
- Chaos testing.
- Security testing.

Output:

Quality Approval.

---

## Stage 9 — Documentation

Owner: Documentation Architect

Activities:

- ADR updates.
- Service specification.
- API documentation.
- Event catalogue.
- Operational runbook.
- Consumer guide.

Output:

Documentation Approval.

---

## Stage 10 — Platform Validation

Owner: DevOps Architect

Activities:

- Container validation.
- CI/CD validation.
- Kubernetes deployment.
- Monitoring configuration.
- Logging configuration.
- Autoscaling validation.
- Backup validation.

Output:

Operational Approval.

---

## Stage 11 — Release

Owner: Release Manager

Activities:

- Review approvals.
- Validate readiness.
- Schedule deployment.
- Execute rollout.
- Monitor deployment.
- Initiate hypercare.

Output:

Production Service.

---

# Mandatory Service Standards

Every microservice SHALL define:

- Service Name
- Business Capability
- Service Owner
- Domain Owner
- API Version
- Event Catalogue
- Dependencies
- Database Ownership
- Health Endpoints
- Readiness Probe
- Liveness Probe
- Metrics
- Logs
- Traces

---

# Communication Standards

Preferred order:

1. Events
2. Asynchronous messaging
3. gRPC
4. REST

Avoid synchronous service chains where possible.

---

# Data Ownership

Every service SHALL:

- Own its database.
- Never access another service's database directly.
- Exchange data through APIs or events.
- Maintain clear ownership boundaries.

---

# Resilience Standards

Every service SHALL include:

- Retry policies.
- Timeouts.
- Circuit breakers.
- Bulkheads.
- Idempotency.
- Dead-letter queues (where applicable).
- Graceful degradation.

---

# Observability Standards

Every service SHALL provide:

- Structured logs.
- Distributed tracing.
- Metrics.
- Health endpoints.
- Readiness probes.
- Liveness probes.
- Correlation IDs.

---

# Quality Gates

The workflow SHALL pause if:

- Architecture review fails.
- Service boundaries are unclear.
- Security review fails.
- Contract tests fail.
- Performance targets fail.
- Documentation is incomplete.
- Operational readiness is not confirmed.

---

# Deliverables

Mandatory artefacts:

- Service Specification
- ADR
- Domain Model
- API Specification
- Event Specification
- Database Design
- Deployment Manifest
- Runbook
- Monitoring Dashboard
- Test Report

---

# Exit Criteria

The workflow completes when:

- Service is deployed.
- Monitoring is active.
- Documentation is published.
- Service registry updated.
- Hypercare begins.

---

# Metrics

Track:

- Deployment Frequency
- Service Availability
- Response Time
- Error Rate
- Event Processing Time
- MTTR
- Consumer Satisfaction
- Operational Incidents

---

# Escalation

Escalate:

Domain conflicts → Domain Architect

Architecture conflicts → Enterprise Architect

Security issues → Security Architect

Operational risks → DevOps Architect

Quality concerns → QA Architect

---

# References

- BUILD_FEATURE.md
- BUILD_API.md
- REVIEW_ARCHITECTURE.md
- AI_EXECUTION_ENGINE.md
- DOMAIN_ARCHITECT.md
- API_ARCHITECT.md
- DATABASE_ARCHITECT.md
- SECURITY_ARCHITECT.md
- DEVOPS_ARCHITECT.md
- QA_ARCHITECT.md
- RELEASE_MANAGER.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise Architecture Office | Initial Build Microservice workflow |
