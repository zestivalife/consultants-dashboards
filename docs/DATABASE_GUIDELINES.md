# Database Guidelines

## Purpose

Rules for database design across Zestiva services.

## Database Philosophy

The database must preserve integrity, tenant isolation, auditability, and long-term maintainability.

## Multi-Tenant Architecture

All tenant-owned data must include organization, tenant, product, or equivalent scoping where applicable.

## Identity Model

`users` stores identity only. Role-specific and business-specific data belongs in profile tables.

## Organization Model

Organizations are first-class entities and own members, subscriptions, packages, services, reports, and assignments.

## Entity Relationship Standards

Use explicit relationships, foreign keys, and clear ownership boundaries.

## Table Naming

Use plural, descriptive table names.

## Column Naming

Use snake_case and consistent suffixes like `_id`, `_at`, `_status`.

## Primary Keys

Use UUID primary keys unless a service has a documented reason not to.

## Foreign Keys

Use foreign keys for same-service relationships. Avoid cross-service foreign keys.

## UUID Standards

UUIDs should be generated consistently by application or database conventions.

## Soft Delete Policy

Use `deleted_at` or status-based deletion for recoverable business entities.

## Audit Fields

Include created/updated timestamps and actor fields where needed.

## Status Fields

Use explicit statuses with documented lifecycle transitions.

## Timestamps

Use timezone-aware timestamps.

## Indexing Strategy

Index foreign keys, frequent filters, search keys, status fields, and unique business identifiers.

## Constraints

Use constraints to protect data integrity, not only application validation.

## Unique Constraints

Use unique constraints for email, scoped slugs, codes, and other natural uniqueness rules.

## Normalization Rules

Normalize identity, roles, permissions, organizations, products, packages, and assignments.

## Denormalization Rules

Denormalize only for performance with documented source of truth.

## Migration Guidelines

Migrations must be additive where possible, reversible, and safe for existing data.

## Alembic Standards

Each migration needs a clear revision, dependency, upgrade, and downgrade.

## Seed Data Guidelines

Seed realistic data only through migrations or approved scripts.

## Transaction Guidelines

Use transactions for multi-step writes and rollback on failure.

## Locking Strategy

Use explicit locking only when concurrency requires it.

## Query Optimization

Avoid N+1 queries, unbounded reads, and missing pagination.

## Pagination Rules

Every list endpoint must support pagination.

## Search Standards

Search must be indexed or bounded for production data sizes.

## Versioning Strategy

Version records where auditability or conflict detection requires it.

## Backup & Recovery Considerations

Production databases must have backups and restore procedures.

## Data Retention Policy

Retention should be documented per data class.

## Archive Policy

Archived data must remain queryable only through controlled paths.

## Database Testing Checklist

- Migration upgrade/downgrade.
- Foreign keys.
- Constraints.
- Indexes.
- Transactions.
- Soft delete.
- Tenant isolation.
