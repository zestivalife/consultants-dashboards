# Build Database Workflow

**Workflow ID:** AI-WF-007
**Version:** 1.0.0
**Status:** APPROVED
**Owner:** Enterprise Architecture Office
**Classification:** Internal
**Parent:** BUILD_FEATURE.md

---

# Purpose

This workflow defines the enterprise standard for designing, implementing, validating, deploying and governing databases throughout their lifecycle.

It applies to relational, document, key-value, graph, time-series and analytical databases.

No production database SHALL be created or modified outside this workflow.

---

# Objectives

- Ensure high-quality data architecture.
- Standardise schema design.
- Enable safe schema evolution.
- Protect enterprise data.
- Optimise performance.
- Ensure recoverability.
- Maintain regulatory compliance.
- Preserve long-term maintainability.

---

# Trigger Conditions

Execute this workflow when:

- A new database is required.
- A schema change is proposed.
- A new microservice requires persistence.
- Data migration is planned.
- Data archival or retention changes are required.

---

# Required Inputs

The workflow SHALL NOT begin until the following artefacts are available:

- Approved Feature Request
- Product Requirements Document (PRD)
- Architecture Decision Record (ADR)
- Domain Model
- Data Classification
- Performance Requirements
- Security Requirements
- Regulatory Requirements

---

# Database Engineering Principles

Every database SHALL be:

- Business-driven
- Secure by default
- Scalable
- Observable
- Recoverable
- Version controlled
- Performance optimised
- Independently governed

---

# Database Lifecycle

```
Requirements
      │
      ▼
Data Modelling
      │
      ▼
Schema Design
      │
      ▼
Architecture Review
      │
      ▼
Migration Planning
      │
      ▼
Implementation
      │
      ▼
Validation
      │
      ▼
Deployment
      │
      ▼
Monitoring
```

---

# Workflow Stages

## Stage 1 — Data Discovery

Owner: Product Architect

Activities:

- Identify business entities.
- Identify data ownership.
- Define retention requirements.
- Classify sensitive information.
- Identify reporting needs.

Output:

Approved Data Requirements.

---

## Stage 2 — Domain Modelling

Owner: Domain Architect

Activities:

- Define aggregates.
- Define entities.
- Define relationships.
- Validate ownership.
- Review consistency boundaries.

Output:

Domain Data Model.

---

## Stage 3 — Database Architecture

Owner: Database Architect

Activities:

- Select database technology.
- Design logical model.
- Design physical model.
- Normalise or denormalise where justified.
- Define indexing strategy.
- Define partitioning strategy.
- Define archival strategy.

Output:

Database Design.

---

## Stage 4 — Migration Planning

Owner: Database Architect

Activities:

- Version schema.
- Plan forward migration.
- Plan rollback migration.
- Validate compatibility.
- Estimate downtime.

Output:

Migration Plan.

---

## Stage 5 — Security Review

Owner: Security Architect

Activities:

- Encryption at rest.
- Encryption in transit.
- Access control.
- Secrets management.
- Audit logging.
- Compliance validation.

Output:

Security Approval.

---

## Stage 6 — Implementation

Owner: Database Architect

Activities:

- Create schema.
- Define constraints.
- Implement indexes.
- Configure replication.
- Configure backups.
- Configure monitoring.

Output:

Working Database.

---

## Stage 7 — Quality Engineering

Owner: QA Architect

Activities:

- Migration testing.
- Data integrity validation.
- Load testing.
- Performance testing.
- Recovery testing.
- Backup validation.

Output:

Quality Approval.

---

## Stage 8 — Documentation

Owner: Documentation Architect

Activities:

- Update ER diagrams.
- Update ADR.
- Update schema catalogue.
- Update data dictionary.
- Document migration procedures.

Output:

Documentation Approval.

---

## Stage 9 — Platform Validation

Owner: DevOps Architect

Activities:

- Infrastructure validation.
- Backup validation.
- Disaster recovery validation.
- Monitoring configuration.
- Capacity validation.

Output:

Operational Approval.

---

## Stage 10 — Release

Owner: Release Manager

Activities:

- Validate approvals.
- Schedule migration.
- Execute deployment.
- Verify production.
- Initiate hypercare.

Output:

Production Database.

---

# Data Modelling Standards

Every database SHALL define:

- Entities
- Relationships
- Primary Keys
- Foreign Keys
- Constraints
- Indexes
- Views
- Stored Procedures (only where justified)
- Ownership

---

# Security Standards

Every database SHALL implement:

- Encryption at rest.
- Encryption in transit.
- Role-based access control.
- Least privilege.
- Audit logging.
- Secret rotation.
- Sensitive data masking.

---

# Performance Standards

Every database SHALL define:

- Index strategy.
- Query optimisation.
- Connection pooling.
- Capacity planning.
- Partitioning.
- Caching strategy.
- Performance baselines.

---

# Backup & Recovery Standards

Every database SHALL define:

- Backup schedule.
- Recovery Point Objective (RPO).
- Recovery Time Objective (RTO).
- Disaster recovery procedure.
- Backup verification.
- Restore testing schedule.

---

# Observability Standards

Every database SHALL expose:

- Query latency.
- Connection utilisation.
- Replication health.
- Storage utilisation.
- Lock contention.
- Slow query logs.
- Backup status.

---

# Quality Gates

The workflow SHALL pause if:

- Data model is incomplete.
- Security review fails.
- Migration plan is missing.
- Backup strategy is not approved.
- Recovery validation fails.
- Performance targets are not met.
- Documentation is incomplete.

---

# Deliverables

Mandatory artefacts:

- Database Architecture
- Logical Data Model
- Physical Data Model
- ER Diagram
- Data Dictionary
- Migration Plan
- Backup Strategy
- Recovery Plan
- Performance Report
- ADR Updates

---

# Exit Criteria

The workflow completes when:

- Database is deployed.
- Monitoring is active.
- Backup validation succeeds.
- Documentation is published.
- Schema registry updated.
- Hypercare begins.

---

# Metrics

Track:

- Query Response Time
- Transaction Throughput
- Backup Success Rate
- Recovery Success Rate
- Storage Growth
- Index Utilisation
- Replication Lag
- Data Integrity Incidents

---

# Escalation

Escalate:

Architecture conflicts → Enterprise Architect

Domain ownership conflicts → Domain Architect

Security concerns → Security Architect

Operational risks → DevOps Architect

Migration risks → Release Manager

---

# References

- BUILD_FEATURE.md
- BUILD_MICROSERVICE.md
- REVIEW_ARCHITECTURE.md
- DATABASE_ARCHITECT.md
- SECURITY_ARCHITECT.md
- QA_ARCHITECT.md
- DEVOPS_ARCHITECT.md
- DOCUMENTATION_ARCHITECT.md
- RELEASE_MANAGER.md

---

# Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise Architecture Office | Initial Build Database workflow |
