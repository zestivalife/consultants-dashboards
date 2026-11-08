# Diet Builder Pre-Publication Stable Baseline — 2026-11-08

## Release identity

This manifest seals the production baseline immediately before the read-only diet-publication investigation. It does not authorize or record a production mutation.

| System | Repository/source | Exact source SHA | Immutable tag |
| --- | --- | --- | --- |
| Consultant frontend | `zestivalife/consultants-dashboards` | `557733522ac2db98b9ef8de594261532b977ec4e` | `diet-builder-pre-publication-stable-2026-11-08` |
| Practice Operations | `zestivalife/consultants-dashboards` | `557733522ac2db98b9ef8de594261532b977ec4e` | `diet-builder-pre-publication-stable-2026-11-08` |
| Fiteatsy backend/mobile source | `zestivalife/Fiteatsy-mobile` | `2f82fbd81fb91bd4bc6a4b1e590a526d8ec8e034` | `diet-builder-pre-publication-stable-2026-11-08` |

The annotated tags were created against the exact commits above, pushed without moving any branch, and verified with `git rev-parse <tag>^{commit}`.

## Serving deployments

### Consultant frontend

- Production domain: `https://consultant.nuetra.in`
- Vercel project: `prj_jAgRanwLFQEoKOYpLOTYR8UuHryk`
- Deployment: `dpl_2pH6eUWqxXcaHETiR5YPW7cSGv27`
- Deployment URL: `consultants-dashboards-ddtp8zcsf.vercel.app`
- State/target: `READY` / `production`
- Runtime `/api/version` SHA: `557733522ac2db98b9ef8de594261532b977ec4e`
- Browser bundle SHA: `557733522ac2db98b9ef8de594261532b977ec4e`
- Browser bundle branch: `codex/p0-external-diet-unrestricted-authoring`

### Practice Operations

- Railway project/environment: `a8bd7357-120a-4e99-8682-2051488b2d28` / `production`
- Service: `practice-operations-service` (`e05f9841-d2ce-4ec1-93eb-6d3bd5ca3a78`)
- Deployment: `4432f92e-1115-46e0-b04d-b4246021937b`
- State: `SUCCESS`, running instance confirmed
- Image digest: `sha256:9e132c1f4b33a735304fe3668971fb154de8fd67a64dc409dba6c9926ee3f77f`
- Deployment source marker: exact SHA `557733522ac2db98b9ef8de594261532b977ec4e`

### Fiteatsy backend

- Railway project/environment: `8ba18169-e239-4925-9009-f53f62c6c508` / `production`
- Service: `Fiteatsy-mobile` (`fa82d077-4a3e-49e6-8edf-cd7c177c3bac`)
- Deployment: `aa1d282b-a6ca-4cbd-b41c-fba6c633c892`
- State: `SUCCESS`, running instance confirmed
- Image digest: `sha256:043429b6ef8ea166633f617d796bbd2b0445dd68d9c9a6386edeb7e909eaecd8`
- Deployment source marker: exact SHA `2f82fbd81fb91bd4bc6a4b1e590a526d8ec8e034`
- Public health: `{"ok":true,"service":"fiteatsy-backend"}`

The installed iOS application build identity was not independently exposed by the production APIs during this seal. The tagged Fiteatsy commit is therefore the backend/mobile source baseline, not a claim about an App Store or locally installed binary.

## Database and migration baseline

- Practice Operations uses its isolated `practice_operations_alembic_version` ledger. The production-compatible source graph ends at `0064_external_practice_clients`; no Alembic operation was run during this seal.
- Fiteatsy production was previously reconciled against its complete 120-entry applied migration ledger. The source baseline preserves the historical ledger files and the forward migration chain through the canonical consultation correction (`0080`).
- This seal did not execute `upgrade`, `downgrade`, `stamp`, DDL, data repair, or a migration-ledger write.
- Database health is evidenced by the running production services and authenticated reads. A direct database connection was not opened for this seal, so no new claim is made about row-level clinical data.

## CI evidence

- Consultant/Practice Operations exact-SHA run: [42474759325](https://github.com/zestivalife/consultants-dashboards/actions/runs/42474759325) — `success`, head SHA `557733522ac2db98b9ef8de594261532b977ec4e`.
- Fiteatsy exact-SHA run: [42468799342](https://github.com/zestivalife/Fiteatsy-mobile/actions/runs/42468799342) — `success`, head SHA `2f82fbd81fb91bd4bc6a4b1e590a526d8ec8e034`.

## Authenticated production verification

Read-only browser verification confirmed:

- secure update and session restoration;
- Consultant Dashboard;
- client roster and selection;
- Client 360 profile and consent-controlled health context;
- nutrition readiness represented as a non-blocking advisory;
- seven meal heads and five governed options per meal (35/35 generated);
- authoritative nutrient values rendered for governed options;
- Save version, exact-version approval, download, and Publish to Client App controls are present;
- publication is guarded while the editor reports unsaved changes;
- no incorrect consultant access-denied or external-practice-authority error is displayed in the verified flow.

The following contracts remain regression protected by exact-SHA CI and must remain mandatory: authentication/session restoration, secure update, Dashboard, roster, Client 360, Leads, tenant and assignment authority, connection and consent, nutrition advisory, seven-meal/five-option structure, governed food resolution, authoritative calculations, component/serving editing, immutable versioning, exact-version self-approval, document download, publication guards, Fiteatsy onboarding/PIN/OTP, Indian Common Food, active-plan ingestion, mobile rendering contracts, and Internal/Senior Consultant workflows.

## Known limitations and outstanding defect

- **The complete Diet Chart Builder mobile publication lifecycle is NOT verified.**
- The observed plan is approved and has persisted options, but the editor reports unsaved changes and disables publication.
- Client 360 reports that Fiteatsy Diet Plan delivery is not enabled while the mobile application reports an active consultant connection but no published plan.
- No publication, consent change, dirty-state override, or real-client clinical write was performed while creating this seal.
- The installed physical mobile binary identity remains unverified.

## Protected work and forward-only rules

- The primary Fiteatsy worktree contains substantial pre-existing tracked and untracked development changes. They are user-owned and were not modified by this seal.
- The primary Consultant worktree contains the protected local modification `services/practice-operations-service/app/fiteatsy_connections.py`. It was not modified or staged.
- Existing branches, worktrees, migrations, food data, authentication, tenant boundaries, assignments, consent, Super Admin authority, Client 360, Internal/Senior workflows, and production aliases are preserved.
- Future work must reproduce a defect, identify the owning component, make the smallest forward-only correction, run the mandatory sealed-baseline regressions, and obtain separate production deployment authorization.
- No revert, reset, force-push, destructive migration, broad replacement, or production-data mutation is permitted.

## Recovery references

- Consultant frontend recovery deployment: `dpl_2pH6eUWqxXcaHETiR5YPW7cSGv27`.
- Practice Operations recovery deployment/image: `4432f92e-1115-46e0-b04d-b4246021937b` / `sha256:9e132c1f4b33a735304fe3668971fb154de8fd67a64dc409dba6c9926ee3f77f`.
- Fiteatsy recovery deployment/image: `aa1d282b-a6ca-4cbd-b41c-fba6c633c892` / `sha256:043429b6ef8ea166633f617d796bbd2b0445dd68d9c9a6386edeb7e909eaecd8`.

These references identify known serving artifacts. They are not authorization to redeploy or roll back automatically.
