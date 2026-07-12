# Platform Owner Console Runtime Audit

Audit date: 2026-07-12
Repository commit: `6eeeb939dc22b1dd4e14ca948c00fd1f144f5ff2`

## Scope

This audit checks whether the Platform Owner Console controls are real runtime integrations rather than placeholder UI. A control is considered working only when it renders, responds to interaction, invokes a named frontend function, calls an existing API through the gateway, reaches an existing backend endpoint, persists to PostgreSQL when it is a write action, returns success, refreshes frontend state, and records an audit event for sensitive writes.

## Classification

- `WORKING`: Full frontend-to-backend path exists in code and is eligible for runtime verification.
- `BROKEN`: Intended integration exists but has a known failure.
- `MOCK`: UI renders from static/mock data and is not backed by a module API.
- `DEAD CODE`: A visible control has no event handler or implementation.
- `NOT CONNECTED`: A control changes local UI state only, or has no matching backend persistence flow.

## Architecture Finding

The owner console has route-backed navigation through `nuetra-frontend/lib/ownerConsoleRoutes.js` and `nuetra-frontend/pages/dashboard/owner/[module].js`.

The active module switch in `nuetra-frontend/components/platform/OwnerConsolePage.jsx` still renders most modules from `platformOwnerConsoleData`. Only these modules are wired through live API hooks:

- People & Access
- Permissions

All other modules currently use static data from `nuetra-frontend/data/platformOwnerConsoleData.js` and should be treated as mock UI until their vertical slices exist.

## Module Matrix

| Module | Route | Data Source | API Client | Gateway Route | Backend Endpoint | PostgreSQL Write | Audit Event | State Refresh | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Command Center | `/dashboard/owner` | `platformOwnerConsoleData` | None | None | None | No | No | Local render only | `MOCK` |
| Organizations | `/dashboard/owner/organizations` | `platformOwnerConsoleData.organizations` | Only unused `createOrganization` helper under People Access | Only `POST /owner/people-access/organizations` | Only create org exists in auth-service People Access | Partial create only | Partial create only | Not wired to module | `MOCK` / `NOT CONNECTED` |
| People & Access | `/dashboard/owner/people-access` | `useOwnerPeopleAccess` | `ownerPeopleAccessAPI` | `/api/v1/owner/people-access/*` | `services/auth-service/app/api/v1/routes/people_access.py` | Yes for writes | Yes in service layer | Yes via hook refresh | `WORKING` in code, requires deployed runtime verification per action |
| Permissions | `/dashboard/owner/permissions` | `useOwnerPeopleAccess.metadata` | `ownerPeopleAccessAPI` | `/api/v1/owner/people-access/roles*` | `people_access.py` role endpoints | Yes | Yes | Metadata refresh after mutation | `WORKING` in code, requires deployed runtime verification per action |
| Package Builder | `/dashboard/owner/packages` | `platformOwnerConsoleData.packages` | None | None | None | No | No | Local selected package only | `MOCK` |
| Service Catalog | `/dashboard/owner/services` | `platformOwnerConsoleData.services` | None | None | None | No | No | Local selected service only | `MOCK` |
| Practitioners | `/dashboard/owner/practitioners` | `platformOwnerConsoleData.practitioners` | None | None | None | No | No | Static render only | `MOCK` |
| Mentors | `/dashboard/owner/mentors` | `platformOwnerConsoleData.mentors` | None | None | None | No | No | Static render only | `MOCK` |
| Consultants | `/dashboard/owner/consultants` | Filtered mock practitioners | None | None | None | No | No | Static render only | `MOCK` |
| Reports | `/dashboard/owner/reports` | `platformOwnerConsoleData.reports` | None | None | None | No | No | Static render only | `MOCK` |
| Audit Logs | `/dashboard/owner/audit` | `platformOwnerConsoleData.auditLogs` | None | None | None | No | No | Static render only | `MOCK` |
| Platform Health | `/dashboard/owner/platform-health` | Hardcoded status cards | None | Version endpoints exist but UI does not call them | Version endpoints exist but UI does not call them | No | No | Static render only | `MOCK` |
| Settings | `/dashboard/owner/settings` | `platformOwnerConsoleData.settings` | None | None | None | No | No | Static render only | `MOCK` |

## Control Matrix

### Command Center

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Export board | Yes | Yes | None | None | `DEAD CODE` |
| Review critical queue | Yes | Yes | None | None | `DEAD CODE` |
| Operational queue cards | Yes | No action | None | None | `MOCK` |

### Organizations

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Generate report | Yes | Yes | None | None | `DEAD CODE` |
| Create organization | Yes | Yes | None | None | `DEAD CODE` |
| Subpage pills | Yes | Yes | `setSubPage` | None | `NOT CONNECTED` |
| Saved Views | Yes | Yes | None | None | `DEAD CODE` |
| Export | Yes | Yes | None | None | `DEAD CODE` |
| Organization roster row | Yes | Yes | `setSelectedId`, `setSubPage` | None | `MOCK` |
| Create organization form inputs | Yes | Editable | Local DOM only | None | `NOT CONNECTED` |

### People & Access

| Control | Rendered | Clickable | Function | API | Backend | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| CSV Import | Yes | Yes | `setShowImportModal`, `handleCsvImport` | `POST /owner/people-access/users/import` | Exists | `WORKING` in code |
| CSV Export | Yes | Yes | `handleCsvExport` | `GET /owner/people-access/exports/users` | Exists | `WORKING` in code |
| Refresh | Yes | Yes | `peopleAccess.refresh` | Summary, metadata, users, invitations | Exists | `WORKING` in code |
| Add mentor / consultant / admin | Yes | Yes | `setShowCreateForm`, `submitCreateUser` | `POST /owner/people-access/users` | Exists | `WORKING` in code |
| KPI filters | Yes | Yes | `applyFilters` | `GET /owner/people-access/users` | Exists | `WORKING` in code |
| Search | Yes | Yes | `applyFilters` | `GET /owner/people-access/users` | Exists | `WORKING` in code |
| Product/status/verification filters | Yes | Yes | `applyFilters` | `GET /owner/people-access/users` | Exists | `WORKING` in code |
| Advanced filters | Yes | Yes | Modal state + `applyFilters` | `GET /owner/people-access/users` | Exists | `WORKING` in code |
| Bulk Activate/Suspend/Deactivate | Yes | Yes | `applyBulkAction` | `POST /owner/people-access/users/bulk-actions` | Exists | `WORKING` in code |
| Bulk Assign role | Yes | Yes | `applyBulkAction` | `POST /owner/people-access/users/bulk-actions` | Exists | `WORKING` in code |
| User row open | Yes | Yes | `openUserDrawer` | `GET /owner/people-access/users/{id}` | Exists | `WORKING` in code |
| Create invitation | Yes | Yes | `submitInvitation` | `POST /owner/people-access/invitations` | Exists | `WORKING` in code |
| Resend invitation | Yes | Yes | `onResendInvitation` | `POST /owner/people-access/invitations/{id}/resend` | Exists | `WORKING` in code |
| Cancel invitation | Yes | Yes | `onCancelInvitation` | `POST /owner/people-access/invitations/{id}/cancel` | Exists | `WORKING` in code |
| Save profile changes | Yes | Yes | `submitUpdateUser` | `PATCH /owner/people-access/users/{id}` | Exists | `WORKING` in code |
| Activate/Suspend selected user | Yes | Yes | `applyBulkAction` | `POST /owner/people-access/users/bulk-actions` | Exists | `WORKING` in code |
| Force logout | Yes | Yes | `onForceLogout` | `POST /owner/people-access/users/{id}/force-logout` | Exists | `WORKING` in code |
| Sync assignments | Yes | Yes | `syncProductAssignments` | `PUT products`, `PUT packages`, `PUT services` | Exists | `WORKING` in code |
| Revoke session | Yes | Yes | `onRevokeSession` | `POST /owner/people-access/users/{id}/sessions/{sessionId}/revoke` | Exists | `WORKING` in code |
| Save attachment | Yes | Yes | `submitAttachment` | `POST /owner/people-access/users/{id}/attachments` | Exists | `WORKING` in code |
| Save note | Yes | Yes | `submitNote` | `POST /owner/people-access/users/{id}/notes` | Exists | `WORKING` in code |

### Permissions

| Control | Rendered | Clickable | Function | API | Backend | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| Save matrix | Yes | Yes | `savePermissions` | `PATCH /owner/people-access/roles/{id}/permissions` | Exists | `WORKING` in code |
| Create custom role | Yes | Yes | `createRole` | `POST /owner/people-access/roles` | Exists | `WORKING` in code |
| Clone role | Yes | Yes | `cloneRole` | `POST /owner/people-access/roles/{id}/clone` | Exists | `WORKING` in code |
| Search permissions | Yes | Yes | Local query + route query | None needed | N/A | `WORKING` local state |
| Expand/collapse | Yes | Yes | Local state | None needed | N/A | `WORKING` local state |
| Permission checkboxes | Yes | Yes | `toggleDraftPermission` | Persisted by Save matrix | Exists | `WORKING` in code |

### Package Builder

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Save draft | Yes | Yes | None | None | `DEAD CODE` |
| Create package | Yes | Yes | None | None | `DEAD CODE` |
| Package row select | Yes | Yes | `setSelectedId` | None | `MOCK` |
| Add section | Yes | Yes | None | None | `DEAD CODE` |
| Edit section | Yes | Yes | None | None | `DEAD CODE` |

### Service Catalog

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Import services | Yes | Yes | None | None | `DEAD CODE` |
| Create service | Yes | Yes | None | None | `DEAD CODE` |
| Service row select | Yes | Yes | `setSelectedId` | None | `MOCK` |

### Practitioners

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Open availability | Yes | Yes | None | None | `DEAD CODE` |
| Add practitioner | Yes | Yes | None | None | `DEAD CODE` |
| Practitioner cards | Yes | No mutation | None | None | `MOCK` |

### Consultants

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Open consultant calendar | Yes | Yes | None | None | `DEAD CODE` |
| Add consultant | Yes | Yes | None | None | `DEAD CODE` |
| Consultant cards | Yes | No mutation | None | None | `MOCK` |

### Mentors

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Export mentor performance | Yes | Yes | None | None | `DEAD CODE` |
| Add mentor | Yes | Yes | None | None | `DEAD CODE` |
| Mentor cards | Yes | No mutation | None | None | `MOCK` |

### Reports

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Saved reports | Yes | Yes | None | None | `DEAD CODE` |
| Export analytics | Yes | Yes | None | None | `DEAD CODE` |
| Report charts | Yes | No mutation | None | None | `MOCK` |

### Audit Logs

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Advanced filters | Yes | Yes | None | None | `DEAD CODE` |
| Export logs | Yes | Yes | None | None | `DEAD CODE` |
| Audit timeline rows | Yes | No mutation | None | None | `MOCK` |

### Platform Health

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Open health report | Yes | Yes | None | None | `DEAD CODE` |
| Run incident review | Yes | Yes | None | None | `DEAD CODE` |
| Health cards | Yes | No mutation | None | None | `MOCK` |

### Settings

| Control | Rendered | Clickable | Function | API | Classification |
| --- | --- | --- | --- | --- | --- |
| Preview workspace | Yes | Yes | None | None | `DEAD CODE` |
| Open settings | Yes | Yes | None | None | `DEAD CODE` |
| Configure setting | Yes | Yes | None | None | `DEAD CODE` |

## Backend Evidence For Wired Areas

People & Access and Permissions have matching backend endpoints in `services/auth-service/app/api/v1/routes/people_access.py`.

The gateway maps `/api/v1/owner/people-access` to auth-service in `api-gateway/app/config.py`.

Owner permission enforcement exists in `api-gateway/app/routers/owner_permissions.py`.

The People & Access service writes audit events for user creation, updates, notes, attachments, invitations, role permission updates, custom roles, role cloning, product/package/service assignments, session revocation, force logout, CSV import, and bulk actions in `services/auth-service/app/services/people_access_service.py`.

## Runtime Verification Status

The frontend production deployment has been verified at commit `6eeeb939dc22b1dd4e14ca948c00fd1f144f5ff2`.

The latest gateway source contains unauthenticated version endpoints, but live gateway verification previously returned `401` for `/api/v1/version` and `/api/v1/versions`. Until the live gateway version endpoint reports the expected commit, deployed end-to-end claims for gateway-mediated owner APIs must remain conservative.

## Required Remediation

1. Keep People & Access and Permissions as the first production vertical slice and runtime-test each mutation with safe test records.
2. Remove or hide dead action buttons from mock modules until their backend APIs exist.
3. Build full vertical slices before exposing controls for Organizations, Packages, Services, Practitioners, Mentors, Consultants, Reports, Audit Logs, Platform Health, and Settings.
4. Add frontend API clients, backend APIs, gateway routes, persistence, audit logging, and state refresh for each non-People module before marking them working.
5. Do not ship static `platformOwnerConsoleData` modules as production functionality.

