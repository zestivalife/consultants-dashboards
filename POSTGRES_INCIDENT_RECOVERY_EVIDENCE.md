# PostgreSQL incident recovery evidence

## Scope and protection state

- Project: `intuitive-sparkle` (`a8bd7357-120a-4e99-8682-2051488b2d28`)
- Environment: `production` (`bb01f5fe-4e68-4121-a563-b493d045604f`)
- PostgreSQL service: `e800ac1e-d873-4717-b7dc-807696c97012`
- Attached restored volume: `1a692ebd-6b8c-41fa-9b97-1866124971d2`
- Attached volume-instance: `2b8f125d-633e-480d-a7fe-cf7d42d59370`
- Original detached volume: `2a96223e-c9e6-4f84-ab41-4756a58fdedd`
- Original volume-instance: `c1189947-806c-4c02-8eef-f743cf6b95f0`
- Mount: `/var/lib/postgresql/data`
- Pre-incident backup: `2efe8063-560c-4516-a27e-d99bffa6663a`
- Incident-state backup: `82915095-50f8-4b6f-83f8-06ead0b26266`

No production attachment, restart, restore, schema migration, data repair, or application deployment was performed during MP-004.

## Timeline

- Pre-incident backup: `2026-10-24T09:34:24.363Z`
- Restore deployment created: `2026-10-24T09:35:16.685Z`
- Restored volume mounted: `2026-10-24T09:36:21.985Z`
- PostgreSQL started: `2026-10-24T09:36:23.011Z`
- PostgreSQL ready: `2026-10-24T09:36:23.931Z`
- Restore deployment: `60bc1e8a-5ca0-4f9e-9a7d-b9c5d1dffb56`

The PostgreSQL log reported automatic recovery and a last-known uptime of `2026-10-20T09:39:40Z`.

## Write-window evidence

Window A is the 52.322 seconds between the backup and restore-deployment creation. Gateway and Practice Operations logs returned no mutation requests, but the detached original volume is not queryable and full WAL history is unavailable. Window A therefore remains unverified.

For Window B, read-only SQL found zero created/updated records after attachment in the inspected identity, membership, documents, plans, appointments, biomarkers, measurements, consultations, goals, tasks, and QA-provisioning tables. Gateway and Practice Operations returned no POST/PUT/PATCH/DELETE entries. PostgreSQL statistics after restart showed zero inserted, updated, or deleted tuples.

Audit limitations:

- `pgaudit.log = none`
- `log_statement = none`
- `wal_level = replica`
- `archive_mode = off`

These limitations prevent claiming complete write-history reconstruction from logs alone.

## Current attached state

- Database: `railway`
- Size: `24,581,823` bytes at investigation time
- Public tables: 243
- Canonical migration head: `0049_global_search_activity`
- Recovery mode: false
- Users: 65
- User roles: 72
- Organisation memberships: 24
- Auth audit rows: 2,079

The state is online and structurally consistent, but it is not proven authoritative until compared with the preserved pre-incident snapshot/original volume.

## Isolation finding

Railway's restore interface accepts a service and environment, but restores by replacing the selected service's volume. It provides no dry-run that cryptographically proves the immutable destination before mutation, and the earlier invocation already selected the production service unexpectedly. Railway CLI exposes attach/detach and file operations, but no supported read-only mount or independent volume-clone operation.

Therefore a second restore was not attempted. Provider-assisted snapshot cloning or an explicitly created disposable service with verified immutable IDs is required.

