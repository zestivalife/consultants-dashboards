# Milestone 2 – Notification Specification

Version: 1.0

Status: Architecture Approved

Owner: Platform Architecture

## Purpose

This document defines notification events for Identity & Onboarding.

Milestone 2 queues notification intent. Direct SMTP, WhatsApp provider integration and delivery retries belong to the Email and Notification Service milestones unless explicitly approved for a slice.

## Delivery Architecture

Application mutation

↓

Domain service

↓

Outbox record in PostgreSQL

↓

Future notification worker

↓

Email or WhatsApp provider

## Channels

- Email
- WhatsApp
- In-app notification
- Future SMS

## Outbox Requirements

Every notification outbox record must include:

- `id`
- `event_type`
- `recipient_user_id`
- `recipient_email`
- `recipient_phone`
- `template_key`
- `payload_json`
- `status`
- `attempt_count`
- `next_attempt_at`
- `created_at`
- `updated_at`
- `sent_at`
- `failed_at`
- `failure_reason`

Allowed statuses:

- `PENDING`
- `PROCESSING`
- `SENT`
- `FAILED`
- `CANCELLED`

## Milestone 2 Events

| Event | Trigger | Channel | Required In Slice |
|---|---|---|---|
| `INVITATION_CREATED` | Invitation created | Email, WhatsApp template | Slice 1 |
| `INVITATION_RESENT` | Invitation resent | Email, WhatsApp template | Slice 1 |
| `INVITATION_EXPIRED` | Invitation expired | In-app, audit only | Slice 1 |
| `INVITATION_ACCEPTED` | Invitee accepts invitation token | Email optional | Slice 2 |
| `INVITATION_REVOKED` | Invitation revoked | In-app, audit only | Slice 2 |
| `INVITATION_OPENED` | Invitee opens invitation link | In-app, audit only | Slice 2 |
| `PASSWORD_CREATED` | Password saved | Email optional | Slice 3 |
| `SESSION_RESTORED` | Session restoration succeeds | In-app optional | Slice 4 |
| `PROFILE_SUBMITTED` | Invitee submits profile | Email, in-app | Slice 5 |
| `DOCUMENT_SUBMITTED` | Document uploaded | In-app | Slice 7 |
| `ONBOARDING_APPROVED` | Reviewer approves | Email, in-app | Slice 8 |
| `ONBOARDING_REJECTED` | Reviewer rejects | Email, in-app | Slice 8 |
| `ACCOUNT_ACTIVATED` | Identity activated | Email | Slice 8 |

## Payload Rules

- Payloads must not contain secrets.
- Invitation plaintext tokens may appear only in transient outbound payload generation and must never be stored as plaintext.
- Outbox records may store invite URLs only if the token is represented by a non-sensitive fingerprint or redacted placeholder.
- All payloads must include `request_id` and source service.

## Retry Rules

Transport retry behavior is future work. Milestone 2 must still persist enough metadata to support retries without schema redesign.
