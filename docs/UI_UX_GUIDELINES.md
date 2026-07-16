# UI/UX Guidelines

## Purpose

Defines the UX and design language for the Zestiva platform.

## Design Philosophy

Enterprise-first, accessible, efficient, and product-aware across Nuetra, FitEatsy, and future products.

## Enterprise-first UX

Prioritize workflows, tables, filters, bulk actions, context panels, and operational clarity.

## Simplicity

Reduce clutter and make common actions obvious.

## Progressive Disclosure

Show advanced controls only when useful.

## Consistency

Use shared components, spacing, typography, and interaction patterns.

## Accessibility

Meet WCAG 2.2 AA expectations.

## Layout

Use predictable page structure: header, actions, filters, content, context drawer.

## Page Hierarchy

Every page should have a clear title, purpose, primary action, and content region.

## App Shell

The shell should provide navigation, breadcrumbs, global search, notifications, workspace/profile controls.

## Navigation Structure

Primary modules must use route-backed navigation.

## Sidebar Rules

Sidebar is for primary modules only.

## Top Navigation Rules

Top navigation is for global search, workspace actions, notifications, quick create, and profile.

## Breadcrumbs

Use breadcrumbs for deep module routes.

## Page Headers

Page headers should include title, context, and primary actions.

## Primary Navigation

Primary navigation must be stable, permission-aware, and product-aware.

## Secondary Navigation

Use contextual navigation inside modules only when needed.

## Tabs

Tabs should not replace route-backed primary navigation.

## Context Menus

Use context menus for row-level and secondary actions.

## Command Palette

Support keyboard-based navigation and quick actions for power users.

## Keyboard Shortcuts

Keyboard shortcuts must be discoverable and not conflict with browser defaults.

## Components

Use reusable buttons, inputs, selects, tables, modals, drawers, cards, badges, tabs, breadcrumbs, toolbars, filters, sidebars, data grids, charts, loading states, empty states, error states, and success states.

## Tables

Tables should support search, filters, sorting, pagination, column visibility, row actions, and bulk actions where appropriate.

## Forms

Long forms belong in drawers, modals, or wizards, not permanently on list pages.

## Drawers

Use drawers for detail views, editing, and contextual workflows.

## Modals

Use modals for focused actions like invite, confirmation, import, and quick create.

## Side Panels

Use side panels for supplementary context and activity timelines.

## Cards

Cards should summarize; they should not replace operational tables.

## Wizards

Use wizards for multi-step flows with progress and resume support.

## Empty States

Empty states must explain what is missing and provide the next action.

## Loading States

Use skeletons or explicit progress for async operations.

## Error States

Errors must be actionable and specific.

## Success States

Success feedback must confirm what changed.

## Toast Notifications

Use toasts for non-blocking feedback.

## Alerts

Use alerts for blocking or high-risk information.

## Validation

Show inline validation and preserve user input.

## Required Fields

Mark required fields clearly.

## Inline Errors

Place errors near the field or action that caused them.

## Auto-save

Use auto-save only when status and recovery are clear.

## Resume Later

Long workflows should support draft or resume behavior.

## Data Tables

Support search, filters, sort, pagination, bulk actions, export, import, column management, and row actions.

## Dashboards

Dashboards should show KPIs, charts, activity feeds, recent actions, and quick actions.

## Responsive Design

Desktop first, tablet optimized, mobile usable.

## Breakpoints

Use consistent breakpoints and verify important workflows at each size.

## WCAG 2.2 AA

Maintain contrast, focus management, semantic labels, and keyboard navigation.

## Screen Readers

Use meaningful labels, headings, and ARIA only where needed.

## Performance UX

Use skeleton loaders, optimistic updates where safe, lazy loading, and infinite scroll only where appropriate.

## Enterprise UX Rules

- Every CTA must work.
- No dead buttons.
- No placeholder pages.
- No mock data in production.
- Every visible action must provide user feedback.
- Every destructive action requires confirmation.
- Every async operation must show progress.
- Every CRUD operation must have success and error states.
- Every page must support deep linking where appropriate.
- Navigation should minimize clicks for common tasks.
- Use role-aware navigation driven by permissions, not hardcoded roles.
- Favor reusable components over one-off implementations.
- Maintain a consistent design system across Nuetra, FitEatsy, and future Zestiva products.
