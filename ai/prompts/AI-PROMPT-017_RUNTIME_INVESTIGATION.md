# Runtime Investigation Prompt

**Document ID:** AI-PROMPT-017

**Version:** 1.0.0

**Status:** APPROVED

**Classification:** Enterprise Investigation Prompt

**Owner:** Enterprise AI Platform Architecture Office

---

# Purpose

This prompt defines the standard investigation methodology for runtime defects across the Enterprise AI Operating System (EAIOS).

It ensures every AI agent follows the same investigation process before making code changes.

The objective is to replace speculative debugging with deterministic root-cause analysis.

---

# Supported Incidents

This prompt SHALL be used for:

- Login Issues
- Authentication Failures
- Authorization Failures
- 401 Unauthorized
- 403 Forbidden
- Permission Issues
- RBAC Issues
- JWT Issues
- Dashboard Routing
- Empty Navigation
- Missing Menus
- API Failures
- Backend Errors
- Frontend Runtime Errors
- Service Communication Issues
- Event Processing Failures
- Notification Failures
- Payment Failures
- Workflow Failures
- Production Bugs

---

# Investigation Principles

The AI SHALL

✓ Never guess

✓ Never assume

✓ Never modify code before investigation

✓ Collect evidence

✓ Verify every assumption

✓ Explain every conclusion

---

# Investigation Lifecycle

```text
Understand Issue
        │
        ▼
Read Documentation
        │
        ▼
Locate Workflow
        │
        ▼
Identify Execution Stage
        │
        ▼
Collect Evidence
        │
        ▼
Determine Root Cause
        │
        ▼
Impact Analysis
        │
        ▼
Fix Strategy
        │
        ▼
Implementation
        │
        ▼
Validation
```

---

# Phase 1

Understand the Problem

Determine

- What happened
- What was expected
- What actually happened
- Who is affected
- Environment
- Product
- User Role
- Module

---

# Phase 2

Read Documentation

Read only the documents relevant to the incident.

Examples

Authentication

↓

Authentication Workflow

RBAC

↓

Roles

Governance

Permissions

Payments

↓

Payment Workflow

Notification

↓

Notification Workflow

Avoid loading unrelated documents.

---

# Phase 3

Locate Execution Workflow

Identify the canonical workflow responsible for the failing functionality.

Examples

Authentication

↓

AI-WORKFLOW-0XX_AUTHENTICATION_AND_AUTHORIZATION_EXECUTION.md

Onboarding

↓

Onboarding Workflow

Assessment

↓

Assessment Workflow

Payment

↓

Payment Workflow

Notification

↓

Notification Workflow

The workflow becomes the execution contract.

---

# Phase 4

Traverse Workflow

Execute every stage sequentially.

Never skip stages.

For every stage verify

Input

↓

Processing

↓

Output

↓

Validation

↓

Dependencies

↓

Logs

↓

Database

↓

API

↓

Frontend

---

# Phase 5

Evidence Collection

Collect

- Source Code
- Runtime Logs
- API Responses
- Database Records
- Configuration
- Environment Variables
- Cache
- Queue Messages
- Event Logs
- Network Calls

Every conclusion must have evidence.

---

# Phase 6

Dependency Analysis

Identify

Downstream

Upstream

Cross-domain

Shared Services

External APIs

Database Dependencies

Events

Queues

Caches

---

# Phase 7

Root Cause Analysis

Determine

Root Cause

NOT Symptoms

Explain

Why

How

When

Impact

Evidence

---

# Phase 8

Fix Strategy

Provide

Immediate Fix

Permanent Fix

Architecture Improvement

Technical Debt

Regression Prevention

---

# Phase 9

Implementation

Only after

✓ Root Cause identified

✓ Evidence collected

✓ Risks evaluated

✓ Dependencies understood

---

# Phase 10

Validation

Verify

Original issue resolved

Regression tests passed

Permissions correct

APIs working

UI working

Events working

Audit logs generated

Monitoring healthy

---

# Mandatory Deliverables

Every investigation SHALL produce

## Executive Summary

---

## Incident Timeline

---

## Workflow Traversal

PASS

FAIL

SKIPPED

---

## Evidence

Files

Logs

APIs

Database

---

## Root Cause

---

## Impact Analysis

---

## Fix Strategy

---

## Files Modified

---

## Validation Results

---

## Risk Assessment

---

## Lessons Learned

---

# Runtime Rules

The AI SHALL

Never jump directly into implementation.

Never recommend random fixes.

Never change multiple systems simultaneously without identifying ownership.

Never ignore architecture.

Never ignore governance.

Never ignore workflows.

Never ignore standards.

---

# Documentation Loading Rules

The AI SHALL first determine the incident category.

Example

Authentication

↓

Load

- Authentication Workflow
- Roles
- Governance
- Registry
- Evaluation

Notification

↓

Load

- Notification Workflow
- Templates
- Governance
- Evaluation

Payment

↓

Load

- Payment Workflow
- Standards
- Registry
- Evaluation

Only relevant documents SHALL be loaded.

---

# Runtime Decision Matrix

```text
Incident
      │
      ▼
Identify Domain
      │
      ▼
Load Workflow
      │
      ▼
Load Supporting Docs
      │
      ▼
Traverse Workflow
      │
      ▼
Collect Evidence
      │
      ▼
Root Cause
      │
      ▼
Fix
      │
      ▼
Validate
```

---

# AI Behaviour Rules

The AI SHALL behave as

Enterprise Architect

↓

System Analyst

↓

Solution Architect

↓

Senior Developer

↓

QA Engineer

↓

Production Support Engineer

↓

Only then

Code Generator

Code generation is the final responsibility, not the first.

---

# Success Criteria

The investigation is complete only when

✓ Exact execution stage identified

✓ Root cause identified

✓ Supporting evidence collected

✓ Owning service identified

✓ Fix plan documented

✓ Validation completed

✓ No assumptions remain

---

# Related Documents

- AI-WORKFLOW-0XX_AUTHENTICATION_AND_AUTHORIZATION_EXECUTION.md
- AI-ROLE-*
- AI-GOV-*
- AI-REGISTRY-*
- AI-EVAL-*
- AI-STD-*
