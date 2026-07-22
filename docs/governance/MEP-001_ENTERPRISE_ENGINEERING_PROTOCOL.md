# MEP-001
# Enterprise Engineering Protocol

Document Version: 1.0
Status: APPROVED
Lifecycle: ACTIVE

---

# Purpose

This document defines the mandatory engineering standards, repository workflow, implementation process, governance rules, and AI operating protocol for the Zestiva One Platform.

Every engineer and every AI implementation must follow this document.

This document does NOT describe feature implementations.

Feature implementations are documented separately under Milestone Specifications (MS).

---

# Source of Truth

Implementation priority:

1. Product Puran
2. Product Architecture
3. PRD
4. Technical Specifications
5. Database Specifications
6. API Specifications
7. Repository Source Code

If conflicts exist:

STOP.

Report the conflict.

Do not make assumptions.

---

# Repository Rules

Before writing code:

• Read repository
• Read Product Puran
• Read milestone document
• Read technical specs
• Identify dependencies
• Identify impacted modules
• Identify impacted APIs
• Identify impacted database
• Produce implementation plan

Wait for approval.

Never write code before repository analysis.

---

# AI Agent Responsibilities

Every AI implementation must:

✓ Read the repository

✓ Understand existing architecture

✓ Reuse existing implementation

✓ Avoid duplicate code

✓ Avoid parallel implementations

✓ Maintain backward compatibility

✓ Update documentation

✓ Build successfully

✓ Run tests

✓ Report risks

✓ Stop after milestone completion

AI agents must never continue into the next milestone without explicit approval.

---

# Repository Modification Rules

Always:

• Extend existing modules

• Reuse services

• Reuse APIs

• Reuse database models

Never:

• Create duplicate authentication

• Create duplicate APIs

• Replace working modules

• Remove unrelated code

---

# Git Workflow

Branch Strategy

main
↓

develop
↓

feature/<feature-name>

Rules

• Never commit directly to main

• Never commit directly to develop

• One milestone per feature branch

• One pull request per milestone

---

# Engineering Workflow

Phase 1

Repository Analysis

↓

Implementation Plan

↓

Approval

↓

Implementation

↓

Validation

↓

Testing

↓

Documentation

↓

Review

↓

Merge

---

# Validation Checklist

Every implementation must:

✓ Build successfully

✓ Pass tests

✓ No lint errors

✓ No broken imports

✓ No broken routes

✓ No security regressions

✓ Documentation updated

---

# Documentation Rules

Every implementation must update:

• Product Bible

• Technical Specification

• API Specification

• Database Specification

• Release Notes

if affected.

Documentation must always match implementation.

---

# Security Rules

Never:

• Store plaintext passwords

• Log secrets

• Hardcode credentials

• Bypass authorization

Always:

• Validate inputs

• Hash passwords

• Sanitize outputs

• Follow least privilege

• Follow OWASP practices

---

# Milestone Rules

Only one milestone may be implemented at a time.

Milestones are independent implementation units.

Every milestone must include:

• Objective

• Scope

• Out of Scope

• Functional Requirements

• Technical Requirements

• Database Changes

• API Changes

• UI Changes

• Testing

• Acceptance Criteria

No milestone may implement functionality from another milestone.

---

# Required Output

Every completed milestone must provide:

• Files Modified

• Files Created

• Files Deleted

• Database Changes

• API Changes

• UI Changes

• Test Results

• Risks

• Breaking Changes

• Migration Steps

• Recommended Next Milestone

Stop after completion.

Wait for approval.

---

# Definition of Done

A milestone is complete only when:

✓ Code builds successfully

✓ Tests pass

✓ Documentation updated

✓ Acceptance criteria satisfied

✓ Security validated

✓ Review completed

✓ Approved for merge
