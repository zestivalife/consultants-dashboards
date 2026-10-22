# Zestiva Internal Consultant Authentication Freeze

## Release identity

- Release identifier: `zestiva-internal-auth-freeze-2026-10-22`
- Freeze date: 22 October 2026
- Freeze authority: Lalit P. Paunikar, Zestiva Super Admin / Product Owner
- Status: **FROZEN — CHANGE CONTROL REQUIRED**
- Production frontend: <https://consultant.nuetra.in>
- Production API gateway: <https://consultant-api.nuetra.in>

This manifest records the verified production state. It does not deploy, migrate,
provision, reset credentials, or change application behaviour.

## Freeze scope

The freeze covers Internal Consultant authentication and Super Admin account
management: login contracts, password verification and recovery, account
provisioning, role and permission assignment, password reset, temporary-password
and first-login flows, sessions, authentication audit logging, owner recovery,
Internal user-management authentication APIs, related Auth database contracts,
Gateway authentication integration, and Internal login frontend behaviour.

The freeze explicitly excludes External Consultant development and Fiteatsy. It
does not modify `api.nuetra.in`. Routine governed account operations and emergency
security incident response remain available.

## Production deployment baseline

| Component | Runtime-reported SHA | Deployment ID | Deployment provenance |
| --- | --- | --- | --- |
| Auth Service | `e602a7be59f592529c2adfd7a4ea9d567b181fa3` | `6b7a5915-68ec-457b-92b3-1bd6f9ebe9cc` | Railway deployment metadata records source commit `68d9de39170de6b08e005e5f49b7f3a16cd4ec9a`, branch `codex/internal-super-admin-iam`, image digest `sha256:64f815af9905511454dbe14ee3adf3a1d21418a064536ff690d6820f0e8e69f6`. The runtime `/version` SHA differs and is retained here as an explicit provenance limitation. |
| API Gateway | `ac6410e8812bf5a8ca78ea87bc9e6b4f3cbd7dbf` | `73d1049a-51f5-4edf-8fca-d245f547801e` | Railway image digest `sha256:9d2dacf48cae1186a8a4d4f704e700c29837cab9326edd4dc7f2de23790562e0`; Railway did not expose a Git commit in deployment metadata, so the runtime `/version` SHA is authoritative evidence. |
| Consultant frontend | `cc4238439df4f728befd04cf2aacfdfdb2812cb6` | `dpl_3gReTYGx7UNYs7brBF8eBk6xKTJy` | Branch `codex/production-login-mfa-step-repair`; deployment URL `consultants-dashboards-as3of3f7l.vercel.app`; production alias `consultant.nuetra.in`. |

The Auth Service and API Gateway were healthy in Railway with one configured and
one running replica each. No service was redeployed to produce this record.

## Database baseline

- Auth database migration head: `b6c7d8e9f0a1`
- Auth user rows: 66
- Active, non-deleted users: 52
- Protected-account duplicate count: one row per protected email
- Protected accounts locked: none
- Unrelated password changes during owner recovery: zero
- Railway Postgres deployment: `992a9018-e916-410b-98bb-ca01b7373afb`
- Railway volume: `postgres-2026-10-20 10:26 UTC`, state `READY`

## Authentication acceptance evidence

| Account | User ID | Role | State | Verified acceptance |
| --- | --- | --- | --- | --- |
| Lalit P. Paunikar | `66f4d9d8-6f1f-4d39-a101-5355d5950002` | `superuser` | ACTIVE, PERMANENT, unlocked | Production password authentication, `/auth/me`, and protected owner People & Access endpoint passed. |
| Priyanshi | `66f4d9d8-6f1f-4d39-a101-5355d5950001` | `superuser` | ACTIVE, PERMANENT, unlocked | Production password authentication, `/auth/me`, and protected owner People & Access endpoint passed. |
| Amit Saini | `e8ac7deb-149f-4358-bfbe-f82fd024a6cf` | `superuser` | ACTIVE, TEMPORARY, unlocked | `must_change_password=true`, no recorded login, and no active session. Interactive first login remains pending and is not claimed as accepted. |

Each protected identity exists exactly once. Amit has one role assignment. Lalit
and Priyanshi retain their existing assignments. The password reset and mandatory
temporary-password replacement routes remain part of the frozen Auth contract.
No plaintext password, token, secret, hash, or session credential is recorded.

## CI evidence

- Frontend exact-SHA CI: GitHub Actions run `39819455829`, completed successfully
  for `cc4238439df4f728befd04cf2aacfdfdb2812cb6`.
- Auth accepted CI evidence: GitHub Actions run `39557177649`, completed
  successfully. The workflow is dispatch-based: GitHub's run-level `head_sha`
  identifies the bootstrap ref, while the job contains successful requested-SHA
  validation, requested-SHA checkout, exact-parity verification, regression, and
  production-build steps. The accepted requested SHA was
  `e602a7be59f592529c2adfd7a4ea9d567b181fa3`.
- Gateway runtime provenance is recorded through the live version endpoint and
  Railway deployment/image identifiers; no separate exact-SHA CI run was located
  for the runtime-reported Gateway SHA during this freeze capture.

## Recovery and rollback references

- Operational checklist: `docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md`
- Release checklist: `docs/RELEASE_CHECKLIST.md`
- Auth application rollback target: Railway deployment
  `6b7a5915-68ec-457b-92b3-1bd6f9ebe9cc`
- Gateway application rollback target: Railway deployment
  `73d1049a-51f5-4edf-8fca-d245f547801e`
- Frontend rollback target: Vercel deployment
  `dpl_3gReTYGx7UNYs7brBF8eBk6xKTJy`
- Database recovery reference: Railway Postgres deployment
  `992a9018-e916-410b-98bb-ca01b7373afb` and the `READY` production volume named
  above. A destructive restore was not performed as part of this read-only freeze.

Rollback must use the existing governed Railway/Vercel procedures and must not
silently reverse the Auth migration or restore production data without an
approved incident/change record.

## Known limitations

1. Amit's first login and temporary-password replacement have not been physically
   completed. They remain required before his interactive login can be accepted.
2. Auth Railway deployment metadata and the Auth runtime `/version` endpoint
   report different source SHAs. Both identifiers are preserved; this freeze does
   not rewrite runtime reporting to conceal the difference.
3. Railway did not expose a Git source SHA for the current Gateway deployment.
4. This is a documentary Git freeze. Repository-wide branch protection was not
   changed because it would affect unrelated, explicitly unfrozen workstreams.

## Change control and reopening

Functional changes require an explicit reopening record from Lalit P. Paunikar
or a separately authorised organisational change-control decision. The record
must identify the requesting authority, reason, proposed change, affected
services, security implications, regression scope, rollback plan, and approval
reference.

Emergency security fixes must follow the documented emergency change-control
process and be recorded as freeze exceptions. A new task or unrelated product
request does not revoke this freeze.

## Seal

The production behaviour and identifiers in this manifest are accepted as the
frozen Internal Consultant Authentication baseline. External Consultant,
Fiteatsy, and other independent product workstreams are outside this seal.
