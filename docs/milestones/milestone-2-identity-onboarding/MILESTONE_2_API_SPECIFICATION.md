# MILESTONE_2_API_SPECIFICATION.md

# Milestone 2 – Identity & Onboarding Platform
## API Specification

Version: 1.0 (Draft)

Status: Approved for Engineering

Owner: Platform Architecture

Related Documents

- MILESTONE_2_IMPLEMENTATION_PLAN.md
- MILESTONE_2_DATABASE_DESIGN.md
- MILESTONE_2_UX_SPECIFICATION.md
- MILESTONE_2_ARCHITECTURE_REVIEW.md
- MILESTONE_2_ACCEPTANCE_REVIEW.md

---

# 1. Purpose

This document defines the complete REST API contract for the Identity & Onboarding Platform.

The specification is implementation-independent.

All APIs shall return consistent response structures.

All protected APIs shall enforce RBAC.

Every mutation shall generate an audit event.

---

# 2. API Standards

Base Path

```
/api/v1
```

Content Type

```
application/json
```

Character Encoding

```
UTF-8
```

API Version

```
v1
```

Authentication

JWT Access Token

Refresh Token

Session Identifier

Correlation ID

```
X-Correlation-ID
```

---

# 3. Standard Response Format

Success

```json
{
  "success": true,
  "message": "",
  "data": {},
  "meta": {},
  "request_id": ""
}
```

Failure

```json
{
  "success": false,
  "message": "",
  "error": {
    "code": "",
    "details": []
  },
  "request_id": ""
}
```

---

# 4. Authentication Headers

Protected APIs

Authorization

```
Bearer {{ACCESS_TOKEN_PLACEHOLDER}}
```

Optional

```
X-Correlation-ID
```

No endpoint shall expose JWT payloads.

---

# 5. Permission Model

Permission format

```
module.action
```

Examples

identity.read

identity.create

identity.update

identity.delete

invitation.send

invitation.cancel

invitation.resend

onboarding.submit

approval.review

approval.approve

approval.reject

role.assign

role.remove

---

# 6. Invitation APIs

Canonical Slice 1 route family:

```
/api/v1/owner/people-access/invitations
```

The earlier `/identity/invitations` namespace is reserved for future internal service APIs and must not replace the existing Owner Console contract during Slice 1.

### Create Invitation

POST

```
/owner/people-access/invitations
```

Authentication

Authenticated

Role Gated

Required Permission

```
users.invite
```

Validation

- Valid email
- Valid role
- Active organization
- Duplicate invitation check

Audit Event

INVITATION_CREATED

Notification

Invitation Email

---

### List Invitations

GET

```
/owner/people-access/invitations
```

Supports

Search

Filter

Sort

Pagination

---

### Get Invitation

GET

```
/owner/people-access/invitations/{id}
```

---

### Resend Invitation

POST

```
/owner/people-access/invitations/{id}/resend
```

---

### Cancel Invitation

POST

```
/owner/people-access/invitations/{id}/cancel
```

---

### Expire Invitation

POST

```
/owner/people-access/invitations/{id}/expire
```

---

# 7. Password Setup APIs

Create Password

POST

```
/identity/password/create
```

Validation

Password Policy

Invitation Token

Token Expiry

Password Confirmation

---

# 8. Email Verification APIs

Verify

POST

```
/identity/email/verify
```

Resend

POST

```
/identity/email/resend
```

---

# 9. Onboarding APIs

Start

POST

```
/onboarding/start
```

Resume

GET

```
/onboarding/session/{id}
```

Save Draft

PATCH

```
/onboarding/session/{id}
```

Next Step

POST

```
/onboarding/session/{id}/next
```

Previous Step

POST

```
/onboarding/session/{id}/previous
```

Submit

POST

```
/onboarding/session/{id}/submit
```

Cancel

POST

```
/onboarding/session/{id}/cancel
```

---

# 10. Document APIs

Upload

POST

```
/documents
```

Replace

PUT

```
/documents/{id}
```

Delete

DELETE

```
/documents/{id}
```

Download

GET

```
/documents/{id}
```

Approve

POST

```
/documents/{id}/approve
```

Reject

POST

```
/documents/{id}/reject
```

---

# 11. Approval APIs

Queue

GET

```
/approvals
```

Approve

POST

```
/approvals/{id}/approve
```

Reject

POST

```
/approvals/{id}/reject
```

Request Changes

POST

```
/approvals/{id}/changes
```

Assign Reviewer

POST

```
/approvals/{id}/assign
```

---

# 12. Identity APIs

Activate

POST

```
/identity/users/{id}/activate
```

Deactivate

POST

```
/identity/users/{id}/deactivate
```

Suspend

POST

```
/identity/users/{id}/suspend
```

Unlock

POST

```
/identity/users/{id}/unlock
```

---

# 13. Role APIs

Assign

POST

```
/roles/assign
```

Remove

POST

```
/roles/remove
```

Switch Active Role

POST

```
/roles/switch
```

List Roles

GET

```
/roles
```

---

# 14. Validation Rules

Email

RFC compliant

Mobile

E.164 format

Password

Minimum 12 characters

Uppercase

Lowercase

Number

Special Character

Invitation Token

Unused

Unexpired

User Status

Must be Active

---

# 15. Error Codes

AUTH_001

Unauthorized

AUTH_002

Token Expired

AUTH_003

Invalid Token

INVITE_001

Invitation Not Found

INVITE_002

Invitation Expired

INVITE_003

Invitation Already Used

ONBOARD_001

Session Not Found

ONBOARD_002

Validation Failed

DOC_001

Invalid Document

DOC_002

Unsupported File

DOC_003

Virus Scan Failed

ROLE_001

Permission Denied

ROLE_002

Invalid Role

---

# 16. Audit Events

INVITATION_CREATED

INVITATION_RESENT

INVITATION_ACCEPTED

INVITATION_CANCELLED

PASSWORD_CREATED

EMAIL_VERIFIED

ONBOARDING_STARTED

ONBOARDING_DRAFT_SAVED

Submitted

Approved

Rejected

Activated

Role Assigned

Role Removed

Login Enabled

---

# 17. Notification Events

Invitation Email

Reminder Email

Verification Email

Approval Email

Rejection Email

Activation Email

---

# 18. Idempotency

Required for

Invitation Create

Invitation Resend

Password Create

Submit Onboarding

Approve

Reject

Activation

---

# 19. Rate Limits

Invitation

20/hour/user

Verification

10/hour/email

Login

Configured by Identity Platform

Upload

Configured by Infrastructure

---

# 20. Security & Secrets Handling

Authentication

JWT Access Token

Refresh Token

Authorization Header

Only placeholders shall be used.

Examples

```
Bearer {{ACCESS_TOKEN_PLACEHOLDER}}
```

Never document

Real JWTs

API Keys

Secrets

Passwords

Connection Strings

SMTP Credentials

Cloud Credentials

Production Hostnames

---

# 21. API Acceptance Criteria

Every endpoint SHALL

Return standard response format

Validate permissions

Validate input

Generate audit event

Return correlation id

Support structured errors

Reject unauthorized requests

No endpoint shall expose internal implementation details.

---

# 22. API Decisions

Document uploads use synchronous metadata creation and asynchronous file processing hooks. Storage provider implementation belongs to the File Storage milestone.

Invitation emails are not retried directly in Slice 1. Slice 1 persists `PENDING` outbox records with retry metadata for the future Email Service worker.

Concurrent onboarding editing is out of scope for Milestone 2.

---

# 23. Cross References

Database

See

MILESTONE_2_DATABASE_DESIGN.md

Implementation

See

MILESTONE_2_IMPLEMENTATION_PLAN.md

UX

See

MILESTONE_2_UX_SPECIFICATION.md

Architecture

See

MILESTONE_2_ARCHITECTURE_REVIEW.md

Acceptance

See

MILESTONE_2_ACCEPTANCE_REVIEW.md
