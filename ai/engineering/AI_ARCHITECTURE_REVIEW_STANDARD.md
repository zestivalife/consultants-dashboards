# Enterprise AI Operating System (EAIOS)
## AI Impact Analysis Standard

Version: 1.0

Status: Mandatory

Priority: High

---

# Purpose

Every implementation affects more than the file being modified.

Before implementing any engineering change, the AI SHALL identify every impacted component, service, dependency and business workflow.

The objective is to prevent regressions, hidden failures and architectural inconsistencies.

Implementation SHALL NOT begin until impact analysis has been completed.

---

# Core Principle

Never analyse files.

Analyse systems.

Every engineering change is a system change.

The AI shall think in terms of:

Business

↓

Architecture

↓

Services

↓

Data

↓

Infrastructure

↓

Users

---

# Mandatory Impact Analysis Categories

The AI SHALL evaluate every applicable category.

---

## Business Impact

Determine:

- Which business capability changes?
- Which user journey changes?
- Which personas are affected?
- Which customer workflows are affected?
- Which business rules change?

Deliverable:

Business Impact Summary

---

## User Impact

Identify:

- User Types
- Roles
- Permissions
- User Experience
- Navigation
- Accessibility

---

## Database Impact

Evaluate:

Tables

Views

Indexes

Constraints

Triggers

Stored Procedures

Migrations

Foreign Keys

Data Integrity

Backwards Compatibility

---

## API Impact

Evaluate:

Endpoints

Contracts

Schemas

Versioning

Authentication

Authorization

Consumers

Producers

Response Models

Error Models

---

## Backend Impact

Evaluate:

Controllers

Services

Repositories

Business Rules

Middleware

Guards

Policies

Validation

Background Jobs

Queues

Schedulers

---

## Microservice Impact

Identify:

Dependent Services

Upstream Services

Downstream Services

Shared Libraries

Shared Contracts

Message Queues

Events

Topics

Consumers

Producers

Service Discovery

---

## Frontend Impact

Evaluate:

Pages

Components

Layouts

Navigation

State Management

Hooks

Forms

Validation

Accessibility

Responsive Behaviour

---

## Mobile Impact

Evaluate:

API Compatibility

Navigation

Offline Behaviour

Caching

Authentication

Push Notifications

Deep Links

---

## Authentication Impact

Evaluate:

Identity

JWT

Sessions

Refresh Tokens

RBAC

Permissions

Capability Bundles

Tenant Resolution

Organisation Resolution

---

## Infrastructure Impact

Evaluate:

Environment Variables

Secrets

Configuration

Load Balancer

API Gateway

Reverse Proxy

Cache

Redis

CDN

Storage

Monitoring

Logging

---

## Security Impact

Evaluate:

Authentication

Authorization

RBAC

Encryption

Secrets

Rate Limiting

Input Validation

Audit Logging

Compliance

---

## Deployment Impact

Evaluate:

CI/CD

Migration Order

Rollback

Feature Flags

Environment Dependencies

Production Verification

Monitoring

---

## Documentation Impact

Determine whether updates are required for:

AI Documents

Architecture

API Specs

Workflow Docs

Runbooks

User Documentation

Developer Documentation

---

# Dependency Mapping

The AI SHALL classify every dependency.

Direct Dependency

Indirect Dependency

Shared Dependency

External Dependency

Optional Dependency

Critical Dependency

---

# Risk Classification

Every implementation SHALL be classified.

LOW

Localized change

Minimal dependency

Low regression risk

---

MEDIUM

Multiple modules affected

Moderate regression risk

---

HIGH

Cross-service impact

Database changes

API changes

Authentication

Authorization

Deployment required

---

CRITICAL

Production risk

Financial impact

Security impact

Compliance impact

Customer data

Infrastructure

Identity

RBAC

---

# Mandatory Questions

Before implementation the AI SHALL answer:

Which business capability changes?

Which APIs change?

Which database objects change?

Which services change?

Which microservices change?

Which frontend components change?

Which mobile screens change?

Which permissions change?

Which infrastructure changes?

Which deployment steps change?

Which documentation changes?

Which downstream systems may fail?

Which upstream systems may fail?

Which regression risks exist?

---

# Impact Matrix

Every task SHALL produce an Impact Matrix.

| Layer | Impact | Risk | Action |
|--------|---------|------|--------|
| Business | Low | Low | Verify |
| Database | None | None | — |
| API | High | High | Regression Tests |
| Backend | Medium | Medium | Validate |
| Frontend | High | High | Runtime Testing |
| Mobile | None | None | — |
| Security | Medium | Medium | Verify |
| Deployment | High | High | Production Verification |

---

# Implementation Permission

Implementation SHALL begin only after:

✓ Impact Analysis Complete

✓ Risk Classification Complete

✓ Dependency Mapping Complete

✓ Repository Standards Verified

✓ Reuse Opportunities Identified

---

# Final Principle

The AI shall never think in terms of modifying code.

The AI shall think in terms of modifying an enterprise system.

Every implementation shall minimise architectural impact, preserve system integrity and protect production stability.
