# PROJECT PRINCIPLES

## Enterprise First

Every feature must support enterprise scalability.

---

## Single Application Platform

Zestiva is one enterprise platform, not separate applications per role.

All users must use the same login page, authentication system, session management system, identity service, routing system, design system and navigation framework.

Role, organization, permissions, licensed modules, assigned data and assigned workflows determine what each user can see and do.

The application shell remains consistent across Super Admin, Corporate Admin, Practitioner, Mentor, Consultant and future roles.

Navigation must be dynamically generated from identity context, permissions, licensed modules, organization configuration and feature flags.

Adding a future role must require configuration, not architectural redesign.

---

## Security by Default

Every API is authenticated.

Every action is authorized.

Every critical event is audited.

---

## API First

Every feature starts with API design.

Frontend consumes APIs.

No frontend business logic duplication.

---

## Workflow Driven

Business processes are implemented as workflows.

Avoid hardcoded flows where configuration is appropriate.

---

## Reusable Components

No duplicate UI.

No duplicate backend logic.

No duplicate database entities.

---

## Modular Architecture

Every module should be independently testable.

Loose coupling.

High cohesion.

---

## Audit Everything

Every critical business action is logged.

---

## Documentation Before Development

Features are specified before implementation.

---

## Backward Compatibility

Avoid breaking APIs or database schema.

Use migrations.

---

## Production Stability

Never sacrifice stability for speed.

Production is always the highest priority.
