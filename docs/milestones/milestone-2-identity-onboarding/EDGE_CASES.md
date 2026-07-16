# Milestone 2 – Edge Cases

Version: 1.0

Status: Architecture Approved

Owner: Platform Architecture

## Invitation Edge Cases

| Case | Expected Behavior |
|---|---|
| Duplicate pending invitation for same email, organization, role and product | Reject with 409 |
| Existing active user invited to same role and scope | Reject with 409 |
| Existing active user invited to new role or organization | Create role-assignment onboarding flow |
| Expired invitation opened | Reject token and show request-new-link guidance |
| Resent invitation | Invalidate previous token hash and create new outbox event |
| Cancelled invitation opened | Reject token and show support guidance |
| Token replay after acceptance | Reject with 410 |
| Malformed token | Reject with 400 and no lookup leakage |

## Password Edge Cases

| Case | Expected Behavior |
|---|---|
| Password below policy | 422 validation response |
| Common password | 422 validation response |
| Password matches last 5 passwords | 422 validation response |
| Multiple failed attempts | Increment failed count and lock at threshold |
| Locked account | Reject login and refresh token |

## Onboarding Edge Cases

| Case | Expected Behavior |
|---|---|
| Browser refresh during wizard | Restore draft from server |
| Template version changes mid-session | Continue using session's pinned template version |
| Required document missing | Block submit |
| Reviewer requests changes | Return session to changes requested state |
| User role changes before activation | Recalculate required template before activation |
| Organization suspended | Block activation and notify reviewer |

## Scope Decisions

- Global templates may be overridden by organization or product templates in future slices.
- A role reassignment resumes onboarding only if the same template version applies.
- Documents are reusable identity assets but every onboarding session must record which document versions satisfied the requirement.
