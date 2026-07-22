# WORKSPACE ARCHITECTURE

---

Document ID      : WORKSPACE_ARCHITECTURE
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

• AGENTS.md
• PROJECT_PRINCIPLES.md
• PRD.md
• TDS.md
• docs/delivery/ROADMAP.md
• docs/delivery/PROJECT_STATE.md
• RBAC_SPECIFICATION.md

---

# PURPOSE

This document defines the Workspace Architecture of the Zestiva Enterprise Platform.

Every authenticated user enters the same application.

The platform dynamically constructs the user's workspace based on identity, organization, permissions, licensed modules and assigned role.

This document governs:

- Login
- Workspace Resolution
- Navigation
- Layout
- Routing
- Module Visibility
- Dashboard Selection
- Authorization
- Future Role Expansion

No feature may violate this architecture.

---

# CORE PRINCIPLE

The platform SHALL operate as ONE Enterprise Application.

There SHALL NOT be separate applications for:

- Super Admin
- Corporate Admin
- Practitioner
- Mentor
- Consultant

There SHALL NOT be separate login systems.

There SHALL NOT be multiple frontend projects.

There SHALL NOT be role-specific URLs.

The platform contains:

✓ One Authentication System

✓ One Session Management

✓ One Identity Service

✓ One Workspace Resolver

✓ One Navigation Framework

✓ One Design System

✓ One Application Shell

Only the Workspace changes.

---

# APPLICATION ENTRY

Every user enters using

/login

Authentication Flow

User

↓

Login

↓

Authentication

↓

JWT

↓

Identity Resolution

↓

Organization Resolution

↓

Role Resolution

↓

Permission Resolution

↓

Workspace Resolution

↓

Navigation Generation

↓

Dashboard Loading

↓

Application Ready

---

# APPLICATION SHELL

Every authenticated user shares the same shell.

The shell contains

Header

Sidebar

Breadcrumb

Workspace Header

Content Area

Notification Center

Profile Menu

Help Center

Footer

No module may replace the application shell.

Modules render only inside the Content Area.

---

# WORKSPACE RESOLVER

The Workspace Resolver determines the complete application experience.

Inputs

Authenticated User

Organization

Role

Permissions

Licensed Modules

Feature Flags

Outputs

Navigation

Dashboard

Routes

Widgets

Quick Actions

Workspace Branding

Visible Modules

Accessible APIs

---

# SUPPORTED WORKSPACES

Super Admin Workspace

Corporate Admin Workspace

Practitioner Workspace

Mentor Workspace

Consultant Workspace

Future

Nutritionist Workspace

Psychologist Workspace

Doctor Workspace

Employee Workspace

Partner Workspace

Vendor Workspace

Support Workspace

Auditor Workspace

API Workspace

Adding a workspace SHALL NOT require architectural redesign.

---

# DASHBOARD RESOLUTION

Every workspace has a default dashboard.

Examples

Super Admin

Platform Overview

Corporate Admin

Corporate Dashboard

Practitioner

Today's Consultations

Mentor

Mentoring Dashboard

Consultant

Client Follow-ups

Dashboard selection SHALL be automatic.

---

# NAVIGATION ARCHITECTURE

Navigation SHALL be generated dynamically.

Never hardcode navigation.

Navigation depends on

Workspace

↓

Role

↓

Permissions

↓

Organization

↓

Licensed Modules

↓

Feature Flags

↓

Sidebar Generation

---

# SIDEBAR STRUCTURE

Dashboard

Identity & Access

People & Access

Invitations

Organizations

Roles

Master Data

Assessments

Nutrition

Programs

Reports

Notifications

Settings

Help

Profile

Future modules may remain disabled.

---

# PAGE STRUCTURE

Every page SHALL contain

Page Title

Page Description

Breadcrumb

Primary Action

Secondary Action

Filters

Search

Content

Empty State

Loading State

Error State

Permission State

---

# ROUTING

Every route SHALL validate

Authentication

↓

Organization

↓

Workspace

↓

Role

↓

Permission

↓

License

↓

Feature Flag

↓

Page Render

Unauthorized routes SHALL NOT render.

---

# MODULE VISIBILITY

Each module exists in one of five states.

Hidden

Disabled

Read Only

Editable

Administrative

Module visibility depends on

Role

Permissions

Organization

Subscription

Feature Flags

---

# PERMISSION RESOLUTION

Permission evaluation order

Authenticated

↓

Organization Active

↓

Workspace

↓

Role

↓

Permission

↓

License

↓

Feature Flag

↓

Business Rules

↓

Access Granted

---

# USER MENU

Profile

Preferences

Language

Theme

Notifications

Sessions

Security

Support

Logout

---

# HEADER

Global Search

Notifications

Workspace Name

Organization

Profile

Quick Actions

Help

Future

AI Assistant

---

# BREADCRUMBS

Every page SHALL generate breadcrumbs automatically.

Example

Dashboard

>

Identity & Access

>

People & Access

>

Create User

---

# ORGANIZATION SWITCHER

Future Ready

If a user belongs to multiple organizations

Display Organization Switcher

Reload Workspace

Refresh Permissions

Refresh Navigation

Refresh Dashboard

Without reauthentication.

---

# MULTI ROLE SUPPORT

Users may have multiple roles.

Example

Practitioner

+

Mentor

The Workspace Resolver SHALL determine

Primary Workspace

Merged Navigation

Merged Permissions

Merged Dashboards

No duplicate menu items.

---

# RESPONSIVE BEHAVIOUR

Desktop

Expanded Sidebar

Tablet

Collapsible Sidebar

Mobile

Drawer Navigation

Application shell remains consistent.

---

# ACCESSIBILITY

WCAG AA

Keyboard Navigation

Focus Management

Screen Reader Labels

Accessible Forms

Accessible Navigation

High Contrast Ready

---

# PERFORMANCE

Lazy Load Modules

Route-level Code Splitting

Skeleton Loading

Navigation Caching

Permission Caching

Workspace Caching

---

# SECURITY

Never expose unauthorized navigation.

Never expose unauthorized routes.

Never expose hidden modules.

Never rely only on frontend permission checks.

Backend SHALL always enforce authorization.

---

# FUTURE EXTENSIBILITY

New modules must integrate into

Workspace Resolver

Navigation Builder

Permission Engine

Application Shell

No module may introduce

Custom Navigation

Custom Layout

Custom Login

Custom Session

Custom Permission Engine

---

# UI CONSISTENCY

Every module SHALL use

Common Header

Common Sidebar

Common Components

Common Buttons

Common Tables

Common Forms

Common Dialogs

Common Notifications

Common Error Screens

Common Empty States

---

# WORKSPACE LIFE CYCLE

Login

↓

Authentication

↓

Workspace Resolution

↓

Navigation Generation

↓

Dashboard Loading

↓

User Interaction

↓

Permission Refresh

↓

Workspace Refresh

↓

Logout

---

# ENGINEERING RULES

Every new feature MUST

Integrate into the existing Workspace Architecture.

Reuse the Application Shell.

Reuse Navigation Builder.

Reuse Workspace Resolver.

Reuse Permission Engine.

Never duplicate application infrastructure.

---

# DEFINITION OF DONE

A module is Workspace compliant when

✓ Navigation integrated

✓ Routes protected

✓ Permissions enforced

✓ Workspace compatible

✓ Responsive

✓ Accessible

✓ Uses common shell

✓ Uses common design system

✓ Supports future extensibility

---

END OF DOCUMENT
