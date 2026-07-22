# Coding Standards

## Purpose

Defines how code is written across the Zestiva platform.

## General Engineering Principles

- Correctness over speed.
- Maintainability over shortcuts.
- Explicit behavior over hidden magic.
- Shared services over duplicated logic.

## SOLID Principles

Design services and components with single responsibility, clear interfaces, substitutable dependencies, focused contracts, and dependency inversion where useful.

## DRY

Do not duplicate business logic, API clients, validation rules, auth logic, or design-system components.

## KISS

Prefer the simplest architecture that satisfies production requirements.

## YAGNI

Do not build speculative abstractions unless the platform requirement is clear.

## Clean Architecture

Separate models, repositories, services, schemas, routes, gateway, and frontend clients.

## Separation of Concerns

Identity, authorization, business profile, product scope, organization scope, and UI state must remain separate.

## Folder Structure Standards

Keep code grouped by service/module. Avoid cross-service imports except through APIs or shared packages designed for that purpose.

## Naming Conventions

Names should describe intent, not implementation detail.

## File Naming

Use predictable, lower-case names for backend files and established project conventions for frontend files.

## Component Naming

React components use PascalCase and describe the UI responsibility.

## Variable Naming

Use descriptive names. Avoid abbreviations except common domain terms.

## Function Naming

Functions should read as actions, for example `createUser`, `resolvePermissions`, `revokeSession`.

## API Naming

Use RESTful, versioned, noun-based URLs.

## Database Naming

Use plural table names, clear foreign keys, consistent status fields, and explicit indexes.

## Error Handling Standards

Return structured errors. Do not swallow exceptions silently.

## Logging Standards

Log request IDs, actor IDs, target IDs, and safe context. Never log secrets or plaintext passwords.

## Comments & Documentation Rules

Comment why, not what. Keep docs close to complex business rules.

## Shared Service Rules

Shared workflows like user creation, password handling, session handling, and audit logging must be centralized.

## Dependency Injection Guidelines

Inject repositories, sessions, clients, and settings where it improves testability.

## Reusability Guidelines

Build reusable components and services only after identifying repeated behavior.

## Performance Standards

Avoid N+1 queries, excessive client renders, oversized bundles, and unnecessary network calls.

## State Management Standards

Keep server state in API-backed hooks. Keep local UI state minimal and route-backed where appropriate.

## React Standards

Use clear component boundaries, accessible controls, stable keys, and predictable effects.

## Next.js Standards

Routes must be bookmarkable, refresh-safe, and compatible with production deployment.

## Python Standards

Use type hints, async patterns consistently, repository/service separation, and explicit transactions.

## Backend Service Standards

Business logic belongs in services. Routes should validate, authorize, delegate, and return responses.

## Microservice Communication Standards

Services communicate through versioned APIs or approved internal clients, not direct cross-service database writes.

## Async Processing Standards

Long-running work should be queued or backgrounded with status visibility.

## Testing Standards

Every business-critical change needs unit or integration tests plus runtime verification.

## Code Review Checklist

- Requirements satisfied.
- Impact understood.
- Tests added/updated.
- Permissions enforced.
- Audit logging included.
- No dead code.
- No mock production behavior.

## Refactoring Rules

Refactor only with regression coverage and clear behavior preservation.

## Deprecated Code Handling

Mark deprecated code with removal plan and replace callers before deletion.

## Dead Code Policy

Remove disconnected components, unused hooks, unused API wrappers, placeholder pages, and fake handlers.
