# APPLICATION INFORMATION ARCHITECTURE

---

Document ID      : APPLICATION_INFORMATION_ARCHITECTURE
Version          : 1.0
Status           : APPROVED
Lifecycle        : FROZEN FOR IMPLEMENTATION

Project          : Zestiva Enterprise Platform

Owner            : Product Owner
Engineering Lead : Codex

Approved By      : Lalit P. Paunikar

Approval Date    : 16 July 2026

Source of Truth  : YES

Last Updated     : 16 July 2026

Related Documents

• WORKSPACE_ARCHITECTURE.md
• PROJECT_PRINCIPLES.md
• docs/delivery/ROADMAP.md
• PRD.md
• TDS.md
• RBAC_SPECIFICATION.md

---

# PURPOSE

This document defines the complete Information Architecture (IA) of the Zestiva Enterprise Platform.

It specifies:

- Modules
- Navigation
- Routes
- Screens
- User journeys
- Workspace organization
- Menu hierarchy

It is the single source of truth for frontend structure.

---

# CORE PRINCIPLES

One Application

One Navigation Framework

One Design System

One Route Hierarchy

One Workspace Architecture

Role-based visibility only.

Never create multiple applications.

---

# APPLICATION STRUCTURE

/login

↓

Application Shell

↓

Workspace

↓

Modules

↓

Pages

↓

Components

---

# PRIMARY NAVIGATION

Dashboard

Identity & Access

Master Data

Assessments

Nutrition

Programs

Appointments

Clients

Reports

Notifications

Settings

Help

Profile

Logout

---

# MODULE STRUCTURE

## Dashboard

Overview

KPIs

Recent Activity

Quick Actions

Tasks

Announcements

---

## Identity & Access

People & Access

Invitations

Organizations

Roles

Permissions

Audit Logs

---

## Master Data

Countries

States

Cities

Languages

Occupations

Specializations

Diseases

Medications

Nutrition Library

Exercise Library

Tags

Lookup Tables

---

## Assessments

Assessment Templates

Question Bank

Assessment Sessions

Assessment Results

Risk Scores

Reports

---

## Nutrition

Nutrition Plans

Meal Library

Recipes

Meal Assignments

Nutrition Analytics

---

## Programs

Programs

Templates

Activities

Milestones

Progress

---

## Appointments

Calendar

Upcoming

Past

Availability

Consultation Rooms

---

## Clients

Client Directory

Client Profile

History

Assessments

Nutrition

Programs

Notes

Files

---

## Reports

Corporate Reports

Practitioner Reports

Client Reports

Export

Analytics

---

## Notifications

Inbox

Email Queue

WhatsApp Queue

Templates

History

---

## Settings

Organization

Branding

Security

Licenses

Integrations

Preferences

---

# SCREEN TYPES

Dashboard

List

Detail

Create

Edit

Wizard

Preview

Approval

Settings

Analytics

History

Audit

Empty State

Error

Loading

---

# PAGE LAYOUT

Header

↓

Breadcrumb

↓

Toolbar

↓

Filters

↓

Content

↓

Pagination

↓

Footer

---

# STANDARD PAGE ACTIONS

Create

View

Edit

Delete

Archive

Export

Import

Search

Filter

Sort

Refresh

Bulk Actions

---

# GLOBAL SEARCH

Search should support

Users

Organizations

Clients

Programs

Assessments

Reports

Master Data

Future modules

---

# USER JOURNEYS

Super Admin

Login

↓

Dashboard

↓

People & Access

↓

Invite User

↓

User Activated

↓

Audit

Corporate Admin

Login

↓

Corporate Dashboard

↓

Employee

↓

Assessment

↓

Reports

Practitioner

Login

↓

Today's Schedule

↓

Client

↓

Assessment

↓

Nutrition Plan

↓

Follow-up

Mentor

Login

↓

Review

↓

Practitioner

↓

Approve

↓

Feedback

Consultant

Login

↓

Client

↓

Nutrition

↓

Progress

↓

Follow-up

---

# ROUTE HIERARCHY

/login

/dashboard

/identity

/identity/people

/identity/invitations

/identity/organizations

/master-data

/assessments

/nutrition

/programs

/appointments

/clients

/reports

/settings

/profile

/help

Future routes must follow this hierarchy.

---

# BREADCRUMB RULES

Generated automatically.

Never hardcoded.

Example

Dashboard

>

Identity

>

People

>

Create User

---

# MENU VISIBILITY

Menu visibility depends on

Workspace

Role

Permissions

Organization

License

Feature Flag

---

# PAGE VISIBILITY

Every page validates

Authentication

↓

Organization

↓

Workspace

↓

Permission

↓

Business Rules

↓

Render

---

# EMPTY STATES

Every module SHALL provide

Illustration

Title

Description

Primary CTA

Secondary CTA

Help Link

---

# ERROR STATES

401

403

404

409

422

500

Service Unavailable

Offline

Each has a consistent design.

---

# RESPONSIVE RULES

Desktop

Tablet

Mobile

Navigation adapts.

Information Architecture remains unchanged.

---

# FUTURE MODULES

Telemedicine

AI Coach

Recovery Intelligence

Marketplace

Billing

CRM

Marketing

Partner Portal

Public API

Mobile

Architecture already supports them.

---

# ENGINEERING RULES

New modules MUST integrate into this hierarchy.

Do not create isolated navigation.

Do not create isolated layouts.

Do not introduce parallel routing structures.

All navigation changes require Product Owner approval.

---

# DEFINITION OF DONE

A module complies with the Information Architecture when

✓ It appears in the correct navigation

✓ It follows the standard route hierarchy

✓ It uses the common layout

✓ It supports breadcrumbs

✓ It supports role-based visibility

✓ It follows workspace architecture

✓ It integrates with the design system

---

END OF DOCUMENT
