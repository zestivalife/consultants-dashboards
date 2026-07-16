# Milestone 2 - Identity & Onboarding Workflow

---

Document Version : 1.0
Status           : APPROVED
Lifecycle        : FROZEN FOR IMPLEMENTATION

Project          : Zestiva Enterprise Platform
Milestone        : Milestone 2

Owner            : Product Owner
Engineering Lead : Codex

Approved By      : Lalit P. Paunikar
Approval Date    : 16 July 2026

Source of Truth  : Yes

Last Updated     : 16 July 2026

Related Documents

• PRD.md
• TDS.md
• ../../PROJECT_STATE.md
• MILESTONE_2_IMPLEMENTATION_PLAN.md
• MILESTONE_2_API_SPECIFICATION.md

---

# DEPLOYMENT_GUIDELINES.md


# Railway Deployment Verification

Before accepting any Railway deployment, verify:

- Repository
- Branch
- Root Directory
- Build Command
- Start Command
- Latest Deployment ID
- Latest Commit SHA
- Build Logs
- Runtime Version Endpoint
- Runtime OpenAPI

A deployment SHALL NOT be accepted until the running service exposes:

GET /api/v1/version

and the reported commit SHA exactly matches the deployed Git commit.


# Deployment Guidelines

Version: 1.0

Status: Approved

Owner: Platform Architecture

Applies To

- Frontend
- API Gateway
- All Backend Services
- Database
- Infrastructure
- Future Microservices

Related Documents

- ../../AGENTS.md
- ../../PROJECT_STATE.md
- ../../RELEASE_CHECKLIST.md
- ../../SECURITY.md
- ../../API_GUIDELINES.md

---

# 1. Purpose

This document defines the mandatory deployment process for every platform component.

No deployment shall be considered complete until runtime verification succeeds.

A successful build DOES NOT mean a successful deployment.

Production acceptance is based on runtime evidence, not build logs.

---

# 2. Deployment Principles

Every deployment must be:

Repeatable

Traceable

Reversible

Observable

Auditable

Verifiable

---

# 3. Deployment Order

Production deployments SHALL follow this sequence.

Database Migration

↓

Backend Services

↓

API Gateway

↓

Frontend

↓

Health Verification

↓

Runtime Verification

↓

Production Acceptance

Deploying components out of order is prohibited unless explicitly approved.

---

# 4. Deployment Strategy

Preferred

Blue/Green

or

Rolling Deployment

Avoid

Manual replacement

Partial deployments

Unknown deployment state

---

# 5. Monorepo Deployment Rules

Every deployable service must define:

Repository

Branch

Root Directory

Build Command

Start Command

Health Endpoint

Version Endpoint

Environment

These values must be documented.

---

# 6. Service Mapping

Every service shall maintain:

Service Name

Repository

Branch

Root Directory

Deployment Platform

Production URL

Health Endpoint

Version Endpoint

Example

Frontend

Repository

<REPOSITORY>

Branch

main

Platform

Vercel

Root Directory

nuetra-frontend

Backend

Repository

<REPOSITORY>

Platform

Railway

Root Directory

services/auth-service

Gateway

Platform

Railway

Root Directory

api-gateway

---

# 7. Branch Policy

Production

main

Development

develop

Feature

feature/<name>

Hotfix

hotfix/<name>

Production deployments SHALL originate only from approved branches.

---

# 8. Version Endpoint

Every backend service SHALL expose

GET

/api/v1/version

Response

{
    "service": "",
    "version": "",
    "commit_sha": "",
    "branch": "",
    "environment": "",
    "build_time": "",
    "migration_version": ""
}

Version endpoints are mandatory.

---

# 9. Health Endpoint

Every service SHALL expose

GET

/api/v1/health

Response

{
    "status": "healthy",
    "service": "",
    "version": "",
    "commit_sha": "",
    "environment": ""
}

Health endpoints shall NOT expose secrets.

---

# 10. Deployment Evidence

Every deployment report SHALL include

Git Commit SHA

Deployment ID

Branch

Repository

Build Number

Environment

Migration Version

Deployment Time

Health Check Result

Version Endpoint Result

Evidence is mandatory.

Statements without evidence are not accepted.

---

# 11. Runtime Verification

Every deployment SHALL verify

Application starts.

Health endpoint responds.

Version endpoint responds.

Expected commit running.

Expected migration running.

Expected routes available.

Authentication works.

Authorization works.

Browser loads.

Console clean.

Network clean.

No runtime exceptions.

---

# 12. Frontend Verification

Verify

Correct Vercel deployment.

Correct commit.

Assets updated.

No stale cache.

No JavaScript errors.

No broken navigation.

No mock data.

---

# 13. Backend Verification

Verify

Correct Railway deployment.

Correct commit.

Correct environment.

Correct migrations.

Correct API routes.

Correct OpenAPI.

No startup errors.

---

# 14. API Gateway Verification

Verify

Routing.

Authentication.

Authorization.

Proxy behaviour.

Headers.

Timeouts.

Correlation IDs.

---

# 15. Database Verification

Verify

Migration version.

Indexes.

Constraints.

Foreign keys.

Data integrity.

Rollback availability.

No manual schema modifications.

---

# 16. Security Verification

Verify

HTTPS

JWT validation

RBAC

Secret loading

Environment variables

No plaintext credentials

No exposed tokens

Sanitized logs

---

# 17. Regression Verification

Mandatory

Login

Logout

Remember Me

Browser Refresh

Browser Restart

Session Restore

Dashboard

Permissions

Navigation

Audit

Notifications

Production issues previously fixed SHALL always be retested.

---

# 18. Browser Verification

Chrome

Firefox

Safari

Edge

Desktop

Tablet

Mobile

---

# 19. Performance Verification

API response

Page load

Database query

Memory

CPU

Connection pool

No obvious regressions.

---

# 20. Rollback Policy

Every deployment SHALL define

Rollback steps

Rollback owner

Rollback trigger

Rollback verification

Rollback time estimate

Rollback shall restore previous production behaviour.

---

# 21. Production Acceptance

Deployment is accepted ONLY when

Build Passed

Deployment Successful

Health Passed

Version Verified

Migration Verified

Runtime Verified

Regression Passed

Security Passed

Audit Passed

Performance Passed

Product Owner Approved

Chief Architect Approved

Engineering Approved

---

# 22. Production Acceptance Report

Every deployment SHALL produce

Deployment Summary

Git Commit

Deployment Platform

Deployment ID

Environment

Migration Version

Health Result

Version Result

Runtime Verification

Regression Results

Known Issues

Rollback Status

Final Decision

Accepted

Rejected

---

# 23. Incident Handling

If deployment fails

Stop rollout.

Identify root cause.

Collect evidence.

Do not guess.

Do not redeploy until root cause is confirmed.

Document findings.

---

# 24. Root Cause Analysis

Every production issue SHALL distinguish

Observed Evidence

Inference

Hypothesis

Only evidence may drive deployment decisions.

Hypotheses must be verified before acting.

---

# 25. Deployment Constraints

Never

Deploy without impact analysis.

Deploy without rollback.

Deploy without migration verification.

Deploy without runtime verification.

Deploy without production evidence.

Mark production ready without acceptance review.

---

# 26. Security & Secrets Handling

Never document or expose

Passwords

JWT Secrets

Private Keys

API Keys

SMTP Credentials

Database Passwords

Cloud Credentials

Access Tokens

Refresh Tokens

Connection Strings

Infrastructure Secrets

Use placeholders only.

Examples

<ENV:DB_PASSWORD>

<ENV:JWT_PRIVATE_KEY>

<ENV:SMTP_API_KEY>

{{ACCESS_TOKEN_PLACEHOLDER}}

---

# 27. Mandatory Engineering Rule

A deployment is NOT considered complete because:

✓ Code compiled

✓ Tests passed

✓ Git push succeeded

✓ Railway built successfully

✓ Vercel deployed successfully

Deployment is complete ONLY after production runtime verification and acceptance.

---

# 28. Definition of Production Ready

A feature is Production Ready only when all of the following are true:

✓ Source code merged.

✓ Build successful.

✓ Deployment successful.

✓ Database migration verified.

✓ Runtime verified.

✓ Regression suite passed.

✓ Security validation passed.

✓ Performance validation passed.

✓ Audit validation passed.

✓ Product Owner acceptance.

✓ Chief Architect acceptance.

Until every condition above is satisfied, the feature status SHALL remain:

IMPLEMENTED

or

LOCALLY VERIFIED

It SHALL NOT be reported as

PRODUCTION READY.
