# API Guidelines

## Purpose

Defines how every API is designed across the Zestiva platform.

## API Philosophy

APIs must be consistent, secure, versioned, observable, and easy for frontend clients to consume.

## REST Standards

Use nouns for resources and HTTP methods for actions.

## URL Naming

Use lowercase, hyphenated paths under a versioned prefix such as `/api/v1`.

## Versioning Strategy

Breaking changes require a new version or backward-compatible transition.

## Request Structure

Requests must use clear DTOs with validation.

## Response Envelope

Use a consistent envelope: `success`, `message`, `data`, `error`, and `request_id`.

## Success Responses

Return the created/updated resource or actionable result.

## Error Responses

Return structured validation, permission, conflict, not found, and server errors.

## Validation Standards

Validate type, format, ownership, scope, and business rules.

## Pagination Standards

List endpoints must include page, limit, total, and has-more metadata.

## Filtering Standards

Support explicit filters with documented names and allowed values.

## Sorting Standards

Support safe sort fields and direction.

## Search Standards

Search must be bounded, indexed where necessary, and tenant-scoped.

## Bulk Operations

Bulk APIs must validate each item, report partial failures, and audit outcomes.

## CRUD Standards

Each production entity should support create, read, update, delete or documented lifecycle equivalent.

## PATCH vs PUT Rules

Use PATCH for partial updates. Use PUT only for full replacement.

## Soft Delete Standards

Prefer soft delete for recoverable business records.

## Restore Endpoints

Provide restore endpoints for soft-deleted records when business workflows require recovery.

## Authentication Requirements

All protected APIs require valid authentication.

## Authorization Requirements

All protected APIs enforce permissions and scope server-side.

## Idempotency Rules

Use idempotency keys for retryable create or payment-like operations.

## Rate Limiting

Rate limit sensitive and high-traffic endpoints.

## API Documentation Standards

Keep request, response, errors, permissions, and examples documented.

## OpenAPI/Swagger Guidelines

Schemas should reflect production DTOs and validation.

## Error Codes

Use standard HTTP codes and stable application error codes where needed.

## Logging Requirements

Log method, path, status, duration, request ID, actor, and target where safe.

## Audit Event Requirements

Mutations must create audit events when they change identity, access, assignments, status, or business-critical data.

## API Testing Standards

Test success, validation, authentication, authorization, not found, conflict, and server errors.

## Performance Targets

APIs should be paginated, avoid N+1 queries, and stay within documented latency targets.

## Backward Compatibility Rules

Avoid removing fields without a migration path.

## Deprecation Policy

Mark deprecated endpoints, provide replacements, and set removal timelines.
