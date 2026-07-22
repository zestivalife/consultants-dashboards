# Security

## Purpose

Security rules for the entire Zestiva platform.

## Security Philosophy

Security must be built into identity, authorization, data access, auditability, and operational workflows from the beginning.

## Authentication Rules

Authentication must be role-neutral. All users use the same login, token, refresh, and session pipeline.

## Authorization Rules

Authorization must be permission-based and scoped by product, organization, tenant, and resource where applicable.

## RBAC Standards

Roles are bundles of permissions. Do not authorize by role name alone.

## Permission Standards

Permissions must be explicit, testable, and enforced server-side.

## Identity Standards

One identity record per human. Business-specific profile data belongs in profile tables.

## Password Policy

Passwords must meet length and complexity requirements and never be stored or logged in plaintext.

## Password Hashing Rules

Use one shared password service. No duplicate bcrypt or hashing logic outside the approved service.

## JWT Standards

JWTs must include only necessary claims and have bounded expiry.

## Refresh Token Rules

Refresh tokens must be stored hashed, rotated, revocable, and tied to sessions.

## Session Management

Support session restore, logout, logout all devices, force logout, and session revocation.

## Remember Me Rules

Remember Me changes persistence duration only; it must not weaken token validation.

## MFA Guidelines

MFA should be supported for privileged users and high-risk actions.

## API Security

All protected APIs require authentication, authorization, validation, rate limiting where appropriate, and structured errors.

## Input Validation

Validate all external input at API boundaries.

## Output Encoding

Encode user-controlled content before rendering.

## CSRF Protection

Use appropriate CSRF protection when cookie-based auth is introduced.

## XSS Prevention

Avoid unsafe HTML injection and sanitize rich text.

## SQL Injection Prevention

Use parameterized queries and ORM-safe patterns.

## Rate Limiting

Rate limit login, password reset, invitation, and sensitive mutation endpoints.

## Secure File Upload Rules

Validate file type, size, ownership, storage path, and access permissions.

## Secret Management

Secrets live in environment variables or secret managers, never in source code.

## Environment Variable Rules

Document required, optional, and production-only variables.

## Audit Logging Requirements

Log identity changes, permission changes, session actions, destructive actions, and high-risk business events.

## Account Lifecycle Rules

Support invited, active, inactive, suspended, locked, and deleted states.

## Invitation Security

Invitation links must expire and be single-purpose.

## Secure Email Links

Email links must avoid leaking secrets and should expire quickly.

## Session Revocation

Revoked sessions and refresh tokens must be rejected immediately.

## Account Lockout Rules

Repeated failed login attempts should lock or throttle accounts safely.

## Data Privacy Guidelines

Collect only necessary data and scope access to the minimum required.

## OWASP Compliance Checklist

Review authentication, access control, injection, cryptographic failures, misconfiguration, vulnerable components, logging, and SSRF risks.

## Security Testing Checklist

- Login brute-force behavior.
- Permission bypass attempts.
- Tenant data isolation.
- Token expiry and refresh.
- File upload validation.
- Sensitive logging review.

## Incident Response Process

Identify, contain, fix, verify, communicate, and document follow-up prevention.
