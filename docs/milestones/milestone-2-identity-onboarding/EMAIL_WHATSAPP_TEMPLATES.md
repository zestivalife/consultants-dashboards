# Milestone 2 – Email and WhatsApp Templates

Version: 1.0

Status: Architecture Approved

Owner: Product Architecture

## Purpose

This document defines message templates used by the Identity & Onboarding Platform.

Templates are content specifications only. Provider integration and actual delivery are future Email Service work unless a slice explicitly includes delivery.

## Template Rules

- Templates must support Nuetra, FitEatsy and future Zestiva products.
- Templates must use variables, not hardcoded product copy.
- Templates must not expose internal IDs unless needed for support.
- Invitation URLs must use HTTPS.
- Plaintext tokens must never be logged or persisted.

## Shared Variables

| Variable | Description |
|---|---|
| `{{product_name}}` | Nuetra, FitEatsy or future product |
| `{{organization_name}}` | Inviting organization |
| `{{recipient_name}}` | Invitee display name |
| `{{inviter_name}}` | Actor sending invitation |
| `{{role_name}}` | Display role |
| `{{invitation_url}}` | One-time invitation link |
| `{{expiry_hours}}` | Invitation expiry window |
| `{{support_email}}` | Support contact |

## Invitation Email

Subject:

`You have been invited to join {{product_name}}`

Body:

`Hello {{recipient_name}},`

`{{inviter_name}} has invited you to join {{organization_name}} as {{role_name}} on {{product_name}}.`

`Use the secure link below to verify your email, create your password and complete onboarding.`

`{{invitation_url}}`

`This invitation expires in {{expiry_hours}} hours. If you were not expecting this invitation, contact {{support_email}}.`

## Invitation WhatsApp Template

`Hello {{recipient_name}}, you have been invited to join {{organization_name}} as {{role_name}} on {{product_name}}. Complete setup here: {{invitation_url}}. This link expires in {{expiry_hours}} hours.`

## Resend Invitation Email

Subject:

`Your {{product_name}} invitation link`

Body:

`Hello {{recipient_name}}, here is your refreshed secure invitation link for {{product_name}}.`

`{{invitation_url}}`

`Only the latest link can be used. Older invitation links are invalid.`

## Activation Email

Subject:

`Your {{product_name}} account is active`

Body:

`Hello {{recipient_name}}, your onboarding has been approved and your account is now active. You can sign in using your registered email.`

## Rejection Or Changes Requested Email

Subject:

`Action required for your {{product_name}} onboarding`

Body:

`Hello {{recipient_name}}, your onboarding submission needs updates before activation. Please sign in using your invitation flow and review the requested changes.`
