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
• ../../delivery/PROJECT_STATE.md
• MILESTONE_2_IMPLEMENTATION_PLAN.md
• MILESTONE_2_API_SPECIFICATION.md

---

# Product Requirements Document (PRD)

Milestone: 2 – Identity & Onboarding Platform

Company: Zestiva LLP

Products: Nuetra, FitEatsy and future Zestiva products

Status: Architecture Documentation In Progress

Canonical Companion: `README.md`

## Document Information

- Product
- Module
- Milestone
- Version
- Status
- Owner
- Stakeholders
- Last Updated

---

# Executive Summary

Zestiva needs one reusable Identity & Onboarding Platform that can create, invite, verify, onboard, approve and activate every operational user type across Nuetra, FitEatsy and future products.

The platform exists to remove manual account setup, prevent role-specific onboarding silos, protect authentication/session stability and provide auditable enterprise governance for every user lifecycle event.

The expected outcome is a template-driven onboarding engine that supports current and future roles without rebuilding authentication, RBAC, documents, approval workflows or notification flows.

Milestone 2 MUST preserve the single application architecture: one login page, one authentication system, one session system, one identity service, one routing system and one design system for all roles.

---

# Vision

Create a reusable Identity & Onboarding Platform that supports every current and future platform role using one configurable onboarding engine.

Every user enters through the same `/login` flow. After authentication, the platform resolves identity, organization, role, permissions, licensed modules, workspace and dashboard destination.

---

# Business Objectives

- Eliminate manual onboarding.
- Reduce onboarding time.
- Centralize identity management.
- Support multi-product users.
- Support multi-role users.
- Support enterprise approval workflows.
- Provide auditability.
- Reduce future development effort.

---

# Business Problem

Current onboarding is manual.

Role onboarding is inconsistent.

Identity is tightly coupled to products.

Future roles would require redevelopment.

No reusable onboarding platform exists.

---

# Success Metrics (KPIs)

- Invitation success rate
- Invitation acceptance rate
- Average onboarding completion time
- Onboarding abandonment rate
- Approval turnaround time
- Account activation time
- Document rejection rate
- Number of support tickets
- Failed onboarding percentage
- Production defects after release

---

# Scope

## In Scope

- Invitation Engine
- Identity Platform
- Single shared login and dashboard resolution flow
- Dynamic workspace resolution based on identity, organization, role, permissions and licensed modules
- Generic Onboarding
- Approval Workflow
- Multi-role Assignment
- Template-driven Forms
- Document Upload
- Identity Activation
- Audit Events
- Notifications

---

## Out of Scope

- Scheduling
- Billing
- Payments
- Clinical Consultation
- AI
- Video Calling
- Chat
- Mobile Application
- Analytics
- External Identity Providers

---

# User Personas

## Super Admin

Responsible for creating organizations, creating users, sending invitations, resetting accounts, suspending users, assigning roles, managing licenses and viewing audit logs.

## Organization Admin

Responsible for organization-scoped administration, user management, invitation management and organization-level reporting within assigned organizations.

## Corporate Admin

Responsible for managing their company, creating employees, inviting employees, viewing assessments, viewing wellness reports and team analytics.

## Practitioner

Responsible for conducting consultations, creating treatment plans, reviewing assessments, managing appointments and viewing assigned clients.

## Mentor

Responsible for reviewing practitioner work, coaching practitioners, quality assurance, escalations and knowledge sharing.

## Consultant

Responsible for client onboarding, lifestyle guidance, nutrition follow-up, wellness tracking and progress monitoring.

## Future Configurable Roles

Future roles must be added through role, permission and onboarding template configuration without changing authentication or session code.

---

# User Journeys

Journey 1

Super Admin creates invitation.

Journey 2

Invitee accepts invitation.

Journey 3

Password creation.

Journey 4

Email verification.

Journey 5

Onboarding completion.

Journey 6

Document upload.

Journey 7

Review.

Journey 8

Approval.

Journey 9

Identity activation.

Journey 10

Dashboard login.

---

# Functional Requirements

FR-001

Super Admin and authorized organization-scoped administrators can invite users according to RBAC scope.

FR-002

Invitation email generated.

FR-003

Invitation expires.

FR-004

Invitation resend.

FR-005

Invitation cancel.

FR-006

Password creation.

FR-007

Password policy.

FR-008

Email verification.

FR-009

Template-driven onboarding.

FR-010

Autosave.

FR-011

Resume onboarding.

FR-012

Upload documents.

FR-013

Approve documents.

FR-014

Request changes.

FR-015

Approve onboarding.

FR-016

Reject onboarding.

FR-017

Activate account.

FR-018

Assign roles.

FR-019

Multiple active roles.

FR-020

Audit events.

Continue until every feature is covered.

---

# Non Functional Requirements

Availability

99.9%

Performance

Page load ≤2 sec

Autosave ≤1 sec

API response ≤500 ms (excluding uploads)

Security

JWT

RBAC

Audit

Password hashing

Scalability

Horizontal scaling

Accessibility

WCAG AA

Localization

Future ready

---

# Business Rules

Invitation

One-time use.

Expiration configurable.

Cannot reuse expired invitation.

Identity

One identity per human.

One identity can have multiple roles.

Onboarding

Template-driven.

Approval

Role based.

Documents

Version controlled.

---

# Assumptions

Email infrastructure available.

Identity Platform operational.

RBAC available.

Audit available.

Notification Service available.

---

# Dependencies

Identity Platform

Workflow Engine

Email Service

Audit Service

Notification Service

RBAC

API Gateway

---

# Risks

Email delivery failure.

Duplicate identities.

Invitation replay.

Approval delays.

Session issues.

Template corruption.

Document upload failures.

---

# Constraints

No hardcoded roles.

No duplicate identity.

No mock production data.

No role-specific onboarding.

Must remain configurable.

---

# Acceptance Criteria

Invitation lifecycle works.

Password creation works.

Email verification works.

Onboarding completes.

Documents upload.

Approval workflow works.

Identity activates.

Dashboard login succeeds.

Multi-role works.

Audit generated.

Regression suite passes.

---

# Traceability Matrix

Requirement

↓

Database

↓

API

↓

UX

↓

Engineering Task

↓

Acceptance Test

---

# Future Enhancements

MFA

SSO

OAuth

SAML

Biometric login

Custom workflows

Dynamic approvals

Custom templates

Offline onboarding

AI document validation

---

# Security & Secrets Handling

This document references authentication and identity workflows only.

No passwords, API keys, JWTs, SMTP credentials, database credentials, or infrastructure secrets shall appear in this document.

Use placeholders only:

<ENV:JWT_PRIVATE_KEY>

<ENV:SMTP_API_KEY>

<ENV:DB_PASSWORD>

{{ACCESS_TOKEN_PLACEHOLDER}}

---

# Cross References

Implementation Plan

Database Design

API Specification

UX Specification

Engineering Task Breakdown

Architecture Review

Acceptance Review
