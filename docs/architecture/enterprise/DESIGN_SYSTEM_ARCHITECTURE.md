# DESIGN SYSTEM ARCHITECTURE

---

Document ID      : DESIGN_SYSTEM_ARCHITECTURE
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

• PROJECT_PRINCIPLES.md
• WORKSPACE_ARCHITECTURE.md
• APPLICATION_INFORMATION_ARCHITECTURE.md
• UX_SPECIFICATION.md

---

# PURPOSE

This document defines the engineering implementation of the Zestiva Design System.

It standardizes every UI element, layout, interaction pattern and component used throughout the platform.

No module may create its own design language.

---

# DESIGN PRINCIPLES

Enterprise First

Minimal Cognitive Load

Consistency Over Creativity

Accessibility by Default

Mobile Responsive

Reusable Components

Scalable Architecture

Performance Focused

---

# DESIGN TOKENS

Typography

Colors

Spacing

Radius

Elevation

Shadows

Borders

Opacity

Animation

Icons

Grid

Breakpoints

Never hardcode these values.

---

# TYPOGRAPHY

Display

Heading

Sub Heading

Body

Caption

Helper

Error

Table

Navigation

Monospace

---


# Typography

The platform shall use **Poppins** as the default typeface across the entire application.

Hierarchy

H1 — 24px — Semi Bold

H2 — 20px — Regular

H3 — 18px — Regular

H4 — 16px — Regular

Body — 14px — Regular

Subtitle — 12px — Regular

Button — 14px — Semi Bold

Label — 12px — Medium

Input — 14px — Regular

Table Header — 12px — Semi Bold

Table Cell — 14px — Regular

The typography scale is global.

Individual pages shall not override font family, size, or weight unless explicitly approved by the Product Owner.


# COLOR SYSTEM

Primary

Secondary

Success

Warning

Danger

Info

Neutral

Background

Surface

Border

Disabled

Focus

Hover

Selected

---

# ICONOGRAPHY

Use one icon library only.

Every action shall have a consistent icon.

Example

Create

Edit

Delete

Archive

Search

Filter

Refresh

Download

Upload

Settings

Notifications

Help

Profile

---

# LAYOUT SYSTEM

Application Shell

↓

Workspace

↓

Page

↓

Section

↓

Card

↓

Component

No page shall bypass this hierarchy.

---

# PAGE TEMPLATE

Every page contains

Header

Description

Breadcrumb

Toolbar

Primary CTA

Secondary CTA

Filters

Search

Content

Pagination

Footer

---

# CRUD STANDARD

Every CRUD module follows

List

↓

Create

↓

View

↓

Edit

↓

Archive

↓

History

↓

Audit

Never invent different CRUD patterns.

---

# TABLE STANDARD

Every table supports

Search

Filters

Sorting

Pagination

Bulk Selection

Column Visibility

Export

Responsive Layout

Loading State

Empty State

Error State

---

# FORM STANDARD

Every form supports

Autosave (where applicable)

Validation

Inline Errors

Required Fields

Helper Text

Keyboard Navigation

Draft Mode

Unsaved Changes Warning

Success Feedback

---

# BUTTONS

Primary

Secondary

Outline

Ghost

Danger

Icon Only

Loading

Disabled

Never invent custom button styles.

---

# INPUT COMPONENTS

Text

Textarea

Password

Email

Phone

Number

Date

Time

Select

Multi Select

Autocomplete

Checkbox

Radio

Toggle

File Upload

Image Upload

Rich Text

Tags

Search

---

# MODALS

Confirmation

Delete

Warning

Information

Success

Error

Wizard

Modal sizes shall be standardized.

---

# DRAWERS

Right Drawer

Left Drawer

Bottom Sheet (Mobile)

Used for

Quick View

Quick Edit

Filters

Details

Never replace full pages unnecessarily.

---

# WIZARDS

Multi-step forms shall use

Progress Indicator

Step Validation

Previous

Next

Save Draft

Finish

Cancel

---

# DASHBOARDS

Every dashboard contains

Summary Cards

Charts

Recent Activity

Tasks

Notifications

Quick Actions

Role-specific Widgets

---

# CARDS

Statistic Card

Profile Card

Information Card

Action Card

Chart Card

Empty Card

---

# FILTERS

Persistent

Saved Filters (future)

Reset

Clear

Applied Filter Count

---

# SEARCH

Global Search

Module Search

Instant Search

Search History (future)

---

# EMPTY STATES

Illustration

Title

Description

Primary CTA

Secondary CTA

Help Link

Never show blank pages.

---

# LOADING STATES

Skeleton Loader

Progress Bar

Spinner

Button Loading

Table Loading

Chart Loading

---

# ERROR STATES

401

403

404

409

422

500

Offline

Timeout

Retry

---

# TOASTS

Success

Warning

Error

Information

Undo (where applicable)

---

# NOTIFICATIONS

Bell

Drawer

Read

Unread

Archive

Priority

Action Buttons

---

# FILE HANDLING

Preview

Upload

Download

Replace

Version History (future)

---

# ACCESSIBILITY

WCAG AA

Keyboard Navigation

Focus Indicators

Screen Reader Labels

Color Contrast

ARIA

---

# RESPONSIVE DESIGN

Desktop

Tablet

Mobile

Component behaviour changes.

Information architecture does not.

---

# ROLE ADAPTATION

The design system remains identical.

Only

Navigation

Widgets

Dashboards

Permissions

Visible Actions

change by role.

---

# ANIMATION

Minimal

Purposeful

Fast

Consistent

No decorative animations.

---

# ENGINEERING RULES

No inline styles.

No duplicate components.

No duplicate patterns.

Every component shall be reusable.

Every module shall consume shared components.

---

# DESIGN TOKENS

Frontend must consume centralized design tokens.

No module may redefine colors, spacing, typography or elevation.

---

# COMPONENT LIBRARY

All UI shall be built from

Foundation

↓

Atoms

↓

Molecules

↓

Organisms

↓

Templates

↓

Pages

Following Atomic Design principles.

---

# DEFINITION OF DONE

A UI implementation is complete when

✓ Uses shared components

✓ Uses design tokens

✓ Responsive

✓ Accessible

✓ Theme Ready

✓ Dark Mode Ready (future)

✓ Matches UX specification

✓ Uses common layouts

✓ No duplicated UI

---

END OF DOCUMENT
