# Milestone 2 – Sequence Diagrams

Version: 1.0

Status: Architecture Approved

Owner: Platform Architecture

## Invitation Creation

```mermaid
sequenceDiagram
    participant Admin as "Super Admin"
    participant UI as "Owner Console"
    participant Gateway as "API Gateway"
    participant Auth as "Auth Service"
    participant DB as "PostgreSQL"
    participant Outbox as "Notification Outbox"
    participant Audit as "Audit Log"

    Admin->>UI: Submit invitation form
    UI->>Gateway: POST /api/v1/owner/people-access/invitations
    Gateway->>Auth: Forward authenticated request
    Auth->>Auth: Validate RBAC users.invite
    Auth->>Auth: Generate secure token
    Auth->>Auth: Hash token and compute fingerprint
    Auth->>DB: Insert user_invitations
    Auth->>Outbox: Insert PENDING invitation email event
    Auth->>Audit: Insert INVITATION_CREATED
    Auth-->>Gateway: Return invitation without plaintext token
    Gateway-->>UI: 201 Created
```

## Invitation Acceptance

```mermaid
sequenceDiagram
    participant Invitee
    participant UI as "Onboarding UI"
    participant Gateway as "API Gateway"
    participant Auth as "Auth Service"
    participant DB as "PostgreSQL"
    participant Audit as "Audit Log"

    Invitee->>UI: Open secure invitation link
    UI->>Gateway: POST /api/v1/onboarding/invitations/validate
    Gateway->>Auth: Forward token validation
    Auth->>DB: Lookup token fingerprint candidates
    Auth->>Auth: Verify token hash
    Auth->>Auth: Validate status, expiry, organization and role
    Auth->>DB: Mark invitation accepted
    Auth->>Audit: Insert INVITATION_ACCEPTED
    Auth-->>UI: Token accepted, redirect target for Password Setup
```

## Password Setup

```mermaid
sequenceDiagram
    participant Invitee
    participant UI as "Onboarding UI"
    participant Gateway as "API Gateway"
    participant Auth as "Auth Service"
    participant DB as "PostgreSQL"
    participant Audit as "Audit Log"

    Invitee->>UI: Create password
    UI->>Gateway: POST /api/v1/onboarding/password
    Auth->>Auth: Validate password policy
    Auth->>Auth: Hash password using shared PasswordService
    Auth->>DB: Update user password
    Auth->>Audit: Insert PASSWORD_CREATED
    Auth-->>UI: Password accepted
```

## Onboarding Approval

```mermaid
sequenceDiagram
    participant User
    participant UI as "Onboarding UI"
    participant Gateway as "API Gateway"
    participant Workflow as "Workflow Service"
    participant DB as "PostgreSQL"
    participant Reviewer
    participant Audit as "Audit Log"

    User->>UI: Submit onboarding
    UI->>Gateway: POST /api/v1/onboarding/sessions/{id}/submit
    Gateway->>Workflow: Forward submission
    Workflow->>DB: Persist submitted state
    Workflow->>Audit: Insert ONBOARDING_SUBMITTED
    Reviewer->>UI: Review queue
    UI->>Gateway: POST /api/v1/onboarding/reviews/{id}/approve
    Workflow->>DB: Approve and activate next state
    Workflow->>Audit: Insert ONBOARDING_APPROVED
```
