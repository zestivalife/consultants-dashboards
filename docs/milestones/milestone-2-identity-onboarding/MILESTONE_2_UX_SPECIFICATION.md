# MILESTONE_2_UX_SPECIFICATION.md

# Milestone 2 – Identity & Onboarding Platform
## UX Specification

Version: 1.0 (Draft)

Status: Approved for UX & Frontend Engineering

Owner: Product Architecture

Related Documents

- MILESTONE_2_IMPLEMENTATION_PLAN.md
- MILESTONE_2_DATABASE_DESIGN.md
- MILESTONE_2_API_SPECIFICATION.md
- MILESTONE_2_ARCHITECTURE_REVIEW.md
- MILESTONE_2_ACCEPTANCE_REVIEW.md

---

# 1. Purpose

This document defines the complete user experience for the Identity & Onboarding Platform.

The objective is to create a consistent, enterprise-grade onboarding experience for all supported roles.

The UX shall be role-aware, template-driven, responsive, and accessible.

No role-specific UI shall be hardcoded.

---

# 2. User Types

Super Admin

Organization Admin

Corporate Admin

Consultant

Practitioner

Mentor

Future Configurable Roles

---

# 3. Primary User Journeys

Journey 1

Super Admin

↓

People & Access

↓

Invite User

↓

Invitation Sent

---

Journey 2

Invitee

↓

Email

↓

Accept Invitation

↓

Verify Email

↓

Create Password

↓

Start Onboarding

↓

Complete Wizard

↓

Submit

↓

Pending Review

---

Journey 3

Reviewer

↓

Pending Queue

↓

Review

↓

Approve

↓

Activate

↓

Dashboard Access

---

# 4. Navigation

Platform

↓

People & Access

↓

Invitations

↓

Onboarding

↓

Approvals

↓

Identity

↓

Roles

↓

Templates

---

# 5. Screen Catalogue

Screen 1

People & Access

Screen 2

Invite User Dialog

Screen 3

Invitation Details

Screen 4

Invitation History

Screen 5

Invitation Expired

Screen 6

Password Setup

Screen 7

Email Verification

Screen 8

Onboarding Dashboard

Screen 9

Onboarding Wizard

Screen 10

Document Upload

Screen 11

Submission Summary

Screen 12

Review Queue

Screen 13

Approval Details

Screen 14

Activation Summary

---

# 6. Invite User Dialog

Fields

- First Name
- Last Name
- Email
- Mobile
- Role
- Product Access
- Organization
- Department
- Language

Buttons

Cancel

Save Draft

Send Invitation

Validation

Required fields

Duplicate email

Duplicate invitation

Invalid role

Loading

Disable buttons

Show progress

Success

Invitation Created

Error

Inline validation

API error banner

---

# 7. Invitation Details

Display

Invitation Status

Sent Date

Expiry Date

Accepted Date

Reminder Count

Audit Timeline

Actions

Resend

Cancel

Expire

---

# 8. Password Setup

Fields

Password

Confirm Password

Validation

Minimum 12 characters

Uppercase

Lowercase

Number

Special Character

Passwords Match

Buttons

Create Password

Cancel

Errors

Expired Token

Weak Password

Already Used

Invalid Token

---

# 9. Email Verification

States

Waiting

Verified

Expired

Invalid

Buttons

Verify

Resend

Back

---

# 10. Onboarding Dashboard

Cards

Profile Completion

Documents

Pending Tasks

Messages

Approval Status

Resume Button

Progress Indicator

---

# 11. Onboarding Wizard

The wizard SHALL be template-driven.

No hardcoded role-specific flow.

Common Navigation

Previous

Next

Save Draft

Exit

Submit

Autosave

Every field change

Every 30 seconds

On step change

Resume

Always resume from last completed step.

---

# 12. Wizard Steps

Step 1

Personal Information

Step 2

Professional Information

Step 3

Specializations

Step 4

Availability

Step 5

Documents

Step 6

Emergency Contact

Step 7

Review

Step 8

Submit

Additional steps may be inserted by template configuration.

---

# 13. Document Upload

Supported Actions

Upload

Replace

Delete

Preview

Download

Retry

Validation

Allowed extensions

Maximum size

Virus scan status

Duplicate detection

Status

Pending

Uploaded

Approved

Rejected

---

# 14. Review Queue

Columns

Applicant

Role

Organization

Submission Date

Current Status

Assigned Reviewer

Priority

Actions

Open

Assign

Approve

Reject

Request Changes

---

# 15. Approval Screen

Sections

Applicant

Timeline

Documents

Comments

Audit

Buttons

Approve

Reject

Request Changes

Assign Reviewer

---

# 16. Dashboard After Approval

Cards

Profile

Roles

Organizations

Products

Notifications

Recent Activity

---

# 17. Loading States

Every async operation shall display:

Skeleton

Spinner

Progress

Loading text

No blank screens.

---

# 18. Empty States

Invitation List

No invitations found.

Review Queue

No pending reviews.

Documents

No documents uploaded.

Notifications

No notifications available.

Each empty state shall include the primary action.

---

# 19. Error States

Network Error

Unauthorized

Forbidden

Session Expired

Validation Error

Unexpected Error

Every error shall provide:

Message

Recovery Action

Retry Button (where applicable)

---

# 20. Accessibility

WCAG 2.2 AA

Keyboard Navigation

Screen Reader Labels

Focus Management

Contrast Compliance

Accessible Error Messages

Logical Tab Order

---

# 21. Mobile Behaviour

Responsive Layout

Single Column Wizard

Bottom Action Bar

Sticky Progress Indicator

Optimized File Upload

Touch Targets Minimum 44px

---

# 22. UX Performance Targets

Initial screen load

≤2 seconds

Wizard navigation

≤500 ms

Autosave feedback

≤1 second

Document upload progress visible within 300 ms

---

# 23. Security & Secrets Handling

The UI shall never display:

Access Tokens

Refresh Tokens

Password Hashes

Internal IDs

Secrets

Infrastructure Information

Sensitive values shall be masked where appropriate.

No browser storage shall expose sensitive credentials beyond the approved authentication model.

---

# 24. Acceptance Criteria

PASS

All required fields validate correctly.

Wizard resumes after browser refresh.

Autosave restores latest draft.

Invitation lifecycle is reflected correctly.

Role-specific template loads successfully.

Approval actions update status without page refresh.

Responsive layout functions correctly.

Accessibility checks pass.

FAIL

Broken navigation.

Lost draft data.

Dead buttons.

Hardcoded role flows.

Mock data.

Unrecoverable errors.

---

# 25. UX Decisions

Collaborative editing is out of scope for Milestone 2.

Reviewers may request changes but must not directly edit applicant-submitted profile fields unless a future approval explicitly adds delegated edit capability.

Applicants must preview the final profile summary before submission.

---

# 26. Cross References

Implementation

See

MILESTONE_2_IMPLEMENTATION_PLAN.md

Database

See

MILESTONE_2_DATABASE_DESIGN.md

API

See

MILESTONE_2_API_SPECIFICATION.md

Architecture

See

MILESTONE_2_ARCHITECTURE_REVIEW.md

Acceptance

See

MILESTONE_2_ACCEPTANCE_REVIEW.md
