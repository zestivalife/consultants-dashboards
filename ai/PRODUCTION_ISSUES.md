# PRODUCTION_ISSUES.md

# Zestiva Enterprise Platform

## Production Issues Register

**Purpose**

This document is the single source of truth for all production issues
identified within the Zestiva platform.

Every production issue must follow the same lifecycle:

1.  Understand
2.  Reproduce
3.  Collect Evidence
4.  Root Cause Analysis (RCA)
5.  Impact Analysis
6.  Design the Fix
7.  Implement
8.  Local Verification
9.  Production Verification
10. Regression Testing
11. Close

------------------------------------------------------------------------

# Issue Status

-   NEW
-   INVESTIGATING
-   ROOT CAUSE IDENTIFIED
-   FIX IN PROGRESS
-   READY FOR VERIFICATION
-   VERIFIED
-   DEPLOYED
-   CLOSED
-   REOPENED

------------------------------------------------------------------------

# Severity

  Severity   Meaning
  ---------- ------------------------------------------
  P0         Production outage / Security / Data loss
  P1         Critical business functionality broken
  P2         Major functionality affected
  P3         Minor issue / UX problem
  P4         Enhancement

------------------------------------------------------------------------

# Issue Template

## PROD-XXX

### Summary

Short description.

### Module

Example: People & Access

### Environment

Production

### Severity

P0 / P1 / P2 / P3 / P4

### Status

NEW

### Reported By

### Reported Date

------------------------------------------------------------------------

## Expected Behaviour

------------------------------------------------------------------------

## Observed Behaviour

------------------------------------------------------------------------

## Steps to Reproduce

1.  
2.  
3.  

------------------------------------------------------------------------

## Evidence

-   Screenshots
-   API responses
-   Logs
-   Browser console
-   Network traces

------------------------------------------------------------------------

## Root Cause Analysis

### Observed Evidence

### Root Cause

### Files Affected

### Database Impact

### API Impact

------------------------------------------------------------------------

## Fix Plan

-   [ ] Backend
-   [ ] Frontend
-   [ ] Database
-   [ ] Documentation
-   [ ] Tests

------------------------------------------------------------------------

## Verification Checklist

-   [ ] Local verification
-   [ ] API verification
-   [ ] UI verification
-   [ ] Production verification
-   [ ] Regression completed

------------------------------------------------------------------------

## Deployment

Commit SHA:

Branch:

Deployment ID:

Environment:

------------------------------------------------------------------------

## Final Outcome

------------------------------------------------------------------------

# Active Issues

  ID         Module            Severity   Status   Owner
  ---------- ----------------- ---------- -------- -------
  PROD-001   People & Access   P1         NEW      

------------------------------------------------------------------------

# Current Priority

## PROD-001

**Title**

People & Access -- Authenticated users receive "Access Denied" after
login.

**Objective**

Identify exactly where access resolution fails (authentication,
organisation, product, role, permissions, routing or API authorisation)
and fix the root cause with full verification.

Status: NEW Priority: P1
