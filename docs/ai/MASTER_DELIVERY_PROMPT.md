# MASTER_DELIVERY_PROMPT.md

# Zestiva One Platform — Enterprise Delivery Standard

Version: 1.0

Purpose:

This document defines the mandatory execution process for all implementation work performed by AI agents within the Zestiva One Platform repository.

This document is a Standard Operating Procedure (SOP).

It must be used together with a specific implementation task (Epic, Feature, Bug, Refactor, Release, etc.).

It is **not** itself an implementation request.

---

# Engineering Mission

Deliver enterprise-grade, production-ready software.

Every implementation must align with:

- Business Requirements
- Product Requirements
- Enterprise Architecture
- Platform Standards
- Security
- Scalability
- Maintainability
- Testability
- Operational Readiness
- Documentation
- Long-term Platform Vision

Never optimise for speed at the expense of engineering quality.

---

# Mandatory Startup

Before making ANY change:

1. Follow AGENTS.md completely.

2. Complete the Repository Startup Sequence.

3. Read every document required by AGENTS.md.

4. Use `DOCUMENT_REGISTRY.md` to locate documentation.

5. Use `SOURCE_OF_TRUTH_MATRIX.md` to identify the authoritative specification.

6. Resolve documentation conflicts using the Conflict Resolution Rule in AGENTS.md.

7. Never guess architecture.

8. Never create duplicate Sources of Truth.

9. Never implement functionality before understanding the architecture.

10. If documentation is outdated, update the appropriate permanent documentation before implementation.

---

# Discovery & Impact Analysis (Mandatory)

Before writing code, analyse and report:

## Business

- Business capability
- Business objective
- Expected user outcomes

## Product

- Existing functionality
- Product impact
- User experience impact

## Architecture

- Impacted applications
- Impacted services
- Shared packages
- APIs
- Database
- Infrastructure
- Deployment
- Security
- Performance
- Observability

## Documentation

Identify every document requiring updates.

## Risks

Identify:

- Technical risks
- Security risks
- Performance risks
- Migration risks
- Backward compatibility concerns
- Dependencies
- Assumptions

Do not begin implementation until the analysis is complete.

---

# Platform Capability Principle

Before creating any new functionality determine whether it belongs to:

- Platform
- Domain
- Product
- Service
- Milestone

Reusable functionality must be implemented as a Platform Capability.

Avoid duplication across products and domains.

---

# Implementation Standards

Every implementation should include where applicable:

- Backend
- Frontend
- Database
- API
- Validation
- Authentication
- Authorisation
- Error Handling
- Structured Logging
- Metrics
- Distributed Tracing
- Audit Logging
- Configuration Management
- Feature Flags
- Background Jobs
- Notifications
- Unit Tests
- Integration Tests
- API Tests
- Runtime Verification

Do not leave:

- TODOs
- Placeholder implementations
- Dead code
- Duplicate functionality

Prefer extending existing services over creating new ones.

---

# Security Requirements

Every implementation must consider:

- Authentication
- Authorisation
- RBAC
- Input Validation
- Output Validation
- Audit Logging
- Secrets Management
- Secure Configuration
- Rate Limiting (where applicable)
- Data Privacy
- Least Privilege

---

# API Standards

Every API must:

- Follow repository API standards.
- Use consistent versioning.
- Validate requests.
- Return consistent responses.
- Return structured error payloads.
- Produce audit events where required.
- Generate appropriate logs and metrics.

---

# Observability Requirements

Every service should support:

- Structured Logging
- Metrics
- Distributed Tracing
- Health Checks
- Readiness Checks
- Error Monitoring

---

# Testing Standards

Implement appropriate tests including:

- Unit Tests
- Integration Tests
- API Tests
- Regression Tests (where applicable)

Verify runtime behaviour before completion.

---

# Documentation Responsibilities

If implementation changes platform behaviour, update the relevant documentation before completing the task.

Potential updates include:

- Governance
- Architecture
- Platform
- Domain
- Product
- Services
- Operations
- API
- Database
- ADRs
- Milestones

Documentation must never fall behind implementation.

---

# Delivery Governance

If implementation changes delivery status, update where applicable:

- DELIVERY_BOARD.md
- PROJECT_STATE.md
- ROADMAP.md
- RELEASE_PLAN.md
- SPRINT_BOARD.md

If a significant architectural decision is made:

Create or update an ADR.

---

# Production Readiness Checklist

Before completion verify:

- Security reviewed
- Performance impact assessed
- Logging verified
- Metrics verified
- Tracing verified
- Error handling verified
- Database migrations validated
- Configuration validated
- Monitoring updated
- Backup & Recovery impact assessed
- CI/CD compatibility verified
- Deployment verified

---

# Quality Standards

Every change must be:

- Production Ready
- Secure
- Observable
- Modular
- Well Tested
- Maintainable
- Backward Compatible
- Fully Documented
- Consistent with Platform Architecture

---

# Completion Report

At task completion provide:

1. Executive Summary

2. Business Capability Delivered

3. Discovery & Impact Analysis Summary

4. Architecture Decisions

5. Files Modified

6. Database Changes

7. APIs Added / Modified

8. Documentation Updated

9. Delivery Documents Updated

10. ADR Required (Yes/No)

11. Tests Executed

12. Runtime Verification Results

13. Security Considerations

14. Performance Considerations

15. Risks

16. Future Improvements

17. Commit Summary

18. Recommended Next Epic

Stop after submitting the completion report.

Do not automatically begin another Epic.

Wait for approval.

---

# Behaviour Without a Task

If this document is provided without a specific implementation request:

- Complete the Repository Startup Sequence.
- Confirm that the repository has been analysed.
- Do not modify code.
- Do not modify documentation.
- Do not infer the next Epic.
- Wait for a specific Epic, Feature, Bug, Refactor or Release request.

This document is an execution standard, not a work order.
