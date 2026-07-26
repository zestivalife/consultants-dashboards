Document ID: PLATFORM-TEMPLATE
Title: Platform Capability Specification Template
Owner: Zestiva Platform Engineering
Status: TEMPLATE
Lifecycle: ACTIVE
Scope: Reusable Platform Capabilities
Applies To: All Platform Capability Specifications
Last Updated: YYYY-MM-DD
Supersedes: None
Depends On: docs/index/REPOSITORY_ARCHITECTURE.md
Related Documents:
- docs/platform/README.md
- docs/architecture/ENTERPRISE_ARCHITECTURE.md

# <Platform Capability Name>

## Purpose

Describe the purpose of this platform capability.

Explain the business problem it solves and why it exists within the Zestiva ecosystem.

---

# Business Context

Describe:

- Business drivers
- Enterprise value
- Consumers
- Expected outcomes

---

# Scope

## In Scope

-

-

-

## Out of Scope

-

-

-

---

# Objectives

- Standardise
- Reuse
- Secure
- Scale
- Simplify
- Govern

---

# Responsibilities

This capability is responsible for:

-

-

-

It is **not** responsible for:

-

-

-

---

# Consumers

List the products, services or domains that consume this capability.

Example:

- Practitioner Platform
- Corporate Platform
- Mentor Platform
- Consultant Platform
- Mobile Applications
- Public APIs

---

# Architecture Overview

Provide a high-level architecture diagram.

```
Consumer

↓

API

↓

Platform Service

↓

Database

↓

Events

↓

Observability
```

---

# Components

Describe each major component.

Example:

## API Layer

Responsibilities

-

-

-

---

## Service Layer

Responsibilities

-

-

-

---

## Data Layer

Responsibilities

-

-

-

---

## Integration Layer

Responsibilities

-

-

-

---

# Functional Capabilities

List all major capabilities.

Example

FC-001

FC-002

FC-003

...

---

# Service Responsibilities

Describe responsibilities owned by this platform.

---

# API Contracts

Document:

- REST APIs
- gRPC
- GraphQL
- Internal APIs

Reference detailed API documentation where applicable.

---

# Data Model

Document major entities.

Example

Entity

Purpose

Owner

Relationships

---

# Event Model

Describe:

Published Events

Consumed Events

Event Flow

Retry Behaviour

Dead Letter Queue behaviour

---

# Security

Document:

Authentication

Authorization

Encryption

Secrets

Compliance

Audit

Privacy

---

# Operational Behaviour

Document:

Scaling

Deployment

Monitoring

Logging

Health Checks

Configuration

Recovery

---

# Non-Functional Requirements

Performance

Availability

Scalability

Reliability

Maintainability

Observability

Security

Accessibility (if applicable)

---

# Dependencies

List:

Platform Dependencies

External Dependencies

Infrastructure Dependencies

---

# Risks

Technical Risks

Operational Risks

Security Risks

Mitigation Strategy

---

# Acceptance Criteria

The capability is considered complete when:

✓

✓

✓

✓

---

# Related Documents

Reference:

Enterprise Architecture

Platform README

API Specifications

ADR

Related Platform Capabilities

---

# Revision History

| Version | Date | Author | Summary |
|----------|------|--------|---------|
| 1.0 | YYYY-MM-DD | | Initial Version |
