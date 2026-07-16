# MILESTONE 2 - IDENTITY & ONBOARDING WORKFLOW

Version: 1.0
Status: Approved
Milestone: 2
Owner: Product Owner
Engineering Owner: Codex
Source of Truth: This document

---

# PURPOSE

This document defines the complete lifecycle for creating, inviting, onboarding, activating, managing and deactivating users within the Zestiva Enterprise Platform.

This document is the authoritative workflow specification.

All backend services, frontend screens, APIs, notifications, database schema, business rules, permissions, and audit events MUST comply with this workflow.

No implementation may contradict this document without Product Owner approval.

---

# BUSINESS OBJECTIVE

Provide a secure, scalable and enterprise-grade onboarding workflow that enables Super Admins to create and onboard all supported user types while maintaining complete auditability and security.

---

# SUPPORTED USER TYPES

## Internal

Super Admin

Platform Administrator

Support Administrator

---

## Business Users

Corporate Admin

Practitioner

Consultant

Mentor

---

## Future

Nutritionist

Psychologist

Doctor

HR Manager

Corporate Employee

API Service Account

---

# USER LIFECYCLE

Every user MUST follow this lifecycle.

Draft

↓

Created

↓

Invitation Generated

↓

Invitation Sent

↓

Invitation Delivered

↓

Invitation Opened

↓

Invitation Accepted

↓

Password Created

↓

Profile Completion

↓

Document Verification (if applicable)

↓

Role Validation

↓

Organization Mapping

↓

Active

↓

First Login

↓

Operational

↓

Inactive

↓

Suspended

↓

Locked

↓

Archived

No state transitions may skip mandatory validation.

---

# ACCOUNT STATUS DEFINITIONS

Draft

User record exists but invitation has not been generated.

Created

User exists.

Invitation not yet sent.

Invited

Invitation generated.

Invitation Sent

Email and/or WhatsApp successfully queued.

Invitation Delivered

Provider confirms delivery.

Invitation Opened

User opened invitation.

Invitation Accepted

Invitation token validated.

Profile Pending

Mandatory profile incomplete.

Documents Pending

Mandatory documents missing.

Verification Pending

Manual approval required.

Active

Fully onboarded.

Inactive

Temporarily disabled.

Suspended

Access blocked.

Locked

Automatically locked due to security policy.

Archived

Historical only.

Cannot login.

---

# USER CREATION WORKFLOW

Actor

Super Admin

Steps

1

Open User Management

↓

2

Select Create User

↓

3

Choose Organization

↓

4

Choose Role

↓

5

Enter User Details

↓

6

Validate Information

↓

7

Create Account

↓

8

Generate Invitation

↓

9

Send Invitation

↓

10

Write Audit Log

↓

11

Notify User

---

# REQUIRED USER INFORMATION

Mandatory

First Name

Last Name

Email

Phone

Country

Timezone

Organization

Role

Status

Language

Optional

Department

Reporting Manager

Designation

Employee Code

Notes

Tags

Profile Photo

---

# ROLE SPECIFIC DATA

## Practitioner

Registration Number

Medical License

Qualification

Specialization

Years of Experience

Clinic

Consultation Type

Availability

Certificates

---

## Consultant

Qualification

Specialization

Languages

Experience

Availability

Region

---

## Mentor

Designation

Area of Expertise

Experience

Certification

Reporting Scope

---

## Corporate Admin

Organization

Department

Business Unit

Designation

Manager

---

# INVITATION WORKFLOW

Create Secure Token

↓

Store Hash

↓

Set Expiry

↓

Generate Email

↓

Generate WhatsApp Template

↓

Queue Notifications

↓

Deliver

↓

Wait For Acceptance

↓

Validate Token

↓

Activate Session

---

# INVITATION RULES

Invitation tokens are single use.

Maximum validity

72 hours.

Expired invitations cannot be reused.

Invitation may be regenerated.

Previous invitation becomes invalid.

Token must never be stored in plain text.

Invitation links must use HTTPS.

Invitation acceptance must be audited.

---

# PASSWORD CREATION

Minimum Length

12

Uppercase

Required

Lowercase

Required

Number

Required

Special Character

Required

Common Password Check

Required

Password History

5 passwords

Maximum Attempts

5

Account Lock

30 minutes

Future

MFA

Passwordless Login

Passkeys

---

# PROFILE COMPLETION

Mandatory

Profile Photo

Gender

DOB

Address

Emergency Contact

Preferred Language

Communication Preferences

Role Specific Fields

100% completion required before Active status.

---

# DOCUMENT UPLOAD

Practitioner

Medical Registration

Medical License

Government ID

Qualification

Consultant

Government ID

Qualification

Mentor

Certification

Government ID

Corporate Admin

Company Authorization

Government ID

Future

Digital Signature

---

# VALIDATION RULES

Email unique

Phone unique

Role mandatory

Organization mandatory

Status mandatory

Invitation token valid

Password compliant

Documents verified

Profile complete

Organization active

Role permitted

---

# SECURITY RULES

Never expose passwords.

Never expose invitation tokens.

Never expose internal IDs.

Never expose JWT secret.

Audit every authentication event.

Encrypt sensitive data.

Rate limit invitations.

Rate limit login.

CSRF protection.

HTTPS only.

---

# PERMISSION MATRIX

Super Admin

Full access.

Corporate Admin

Manage only users inside own organization.

Practitioner

Own profile only.

Consultant

Own profile only.

Mentor

Own profile.

Assigned practitioners.

No cross organization access.

---

# ORGANIZATION RULES

Every user belongs to one organization.

Organization determines

Branding

Permissions

Reporting

Notifications

Policies

Users cannot move organizations without approval.

---

# NOTIFICATION EVENTS

User Created

Invitation Generated

Invitation Sent

Invitation Accepted

Password Set

Profile Completed

Documents Uploaded

Documents Approved

Account Activated

Account Suspended

Password Reset

Login Alert

---

# AUDIT EVENTS

Create User

Update User

Delete User

Invite User

Resend Invite

Accept Invite

Reject Invite

Profile Update

Role Change

Status Change

Login

Logout

Failed Login

Password Reset

Document Upload

Document Approval

Every audit record must contain

Timestamp

Actor

Target User

Organization

IP

Device

Browser

Correlation ID

---

# FAILURE SCENARIOS

Expired Invitation

↓

Offer Resend

Invalid Token

↓

Show Error

↓

Audit

Duplicate Email

↓

Reject Creation

Duplicate Phone

↓

Reject Creation

Organization Disabled

↓

Reject Login

Suspended User

↓

Reject Login

Locked User

↓

Unlock Workflow

---

# API REQUIREMENTS

POST /users

POST /users/invite

POST /users/resend-invite

POST /users/accept-invite

POST /users/set-password

POST /users/complete-profile

POST /users/upload-documents

GET /users/me

GET /users/profile

PATCH /users/profile

GET /users/status

POST /users/activate

POST /users/deactivate

POST /users/suspend

POST /users/unlock

---

# DATABASE REQUIREMENTS

Tables

users

organizations

roles

permissions

user_profiles

user_documents

user_invitations

audit_logs

notification_queue

session_tokens

---

# UI SCREENS

Create User

User Details

Invitation Preview

Invitation History

Accept Invitation

Create Password

Profile Completion

Document Upload

Verification Pending

Welcome Screen

Dashboard Redirect

User Management

---

# SUCCESS CRITERIA

A new user can be fully onboarded without manual engineering intervention.

Every transition is audited.

Every role follows the same workflow.

No orphan accounts exist.

No duplicate identities exist.

Production security standards are maintained.

---

# DEFINITION OF DONE

✓ Workflow implemented.

✓ APIs implemented.

✓ Database implemented.

✓ Frontend implemented.

✓ UX approved.

✓ Tests passing.

✓ Audit logging verified.

✓ Notifications verified.

✓ Documentation updated.

✓ Production deployment verified.

This document is the master workflow specification for Identity & Onboarding.
