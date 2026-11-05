# P0 integrated-staging foundation

## Release boundary

- Consultant consumer: `b888da3c63c2595b35cb653d428109aa72bf2422`
- Fiteatsy provider: `f7762c1eed4c3026913028742655d6c3f5a6e38e`
- Existing successful consumer CI: run `41983599424`
- The checked-in manifest is deliberately build-pending and therefore cannot deploy. Each of the nine image entries must contain the expected source SHA, immutable registry digest and `tested: true` evidence before the fail-closed validator passes.

## Topology and reuse decision

The isolated environment contains nine application services: Consultant frontend, Gateway, Auth, Profile, Practice Operations, Assessment, Nutrition, Scoring and Fiteatsy backend. PostgreSQL and Redis are dedicated staging resources, not shared with production.

Read-only Railway inventory found reusable service definitions but no currently verified integrated environment spanning both projects. The Consultant project's recovery environments and the Fiteatsy project's QA environments must not be reused until their database targets, provider SHA and isolation are independently verified. No resource was created or changed.

## Immutable workflow

1. Build every image from the manifest SHA with OCI labels for revision and repository.
2. Scan and test that exact digest; never rebuild during promotion.
3. Record the registry digest and successful test result in the manifest.
4. Run `python scripts/validate_staging_release.py --check-no-production-dns`.
5. Deployment automation accepts only `image@sha256:...`; tags are informational only.
6. After deployment, compare runtime image digest and `/version` SHA with the manifest. Any mismatch blocks acceptance.

## Synthetic acceptance identities

- Two consultant tenants (`consultant-a@example.test`, `consultant-b@example.test`).
- One unconnected client, one connected/consented client, one revoked-consent client and one expired-consent client per tenant.
- Cross-tenant negative fixtures, expired sessions and dependency-unavailable cases.
- Email, SMS and WhatsApp are routed only to local sinks; no real addresses or provider credentials are allowed.

## Resource and idle policy

Start application services at 0.25 vCPU/256 MiB, PostgreSQL at 0.5 vCPU/512 MiB with 2 GB volume, and Redis at 0.25 vCPU/256 MiB with 1 GB. Enable sleep for stateless applications when inactive; retain databases at their minimum safe allocation. Raise limits only from observed staging telemetry.

At Railway's published usage rates ($20/vCPU-month, $10/GB RAM-month, $0.15/GB volume-month), continuously allocated maxima are approximately $7.50 per application service, $15.00 PostgreSQL, $7.50 Redis and $0.45 storage: **$90.45/month** before egress for nine applications plus data services. Usage-based sleep can reduce this materially; it is not a guaranteed bill. Any Pro workspace minimum and egress are additional.

## Deployment-readiness checklist

- [x] Production Practice schema inspected in a PostgreSQL-enforced read-only session.
- [x] Production revision is `0064_external_practice_clients`; expected 0061/0063/0064 tables, columns, constraints, indexes and common ownership are present.
- [x] Nine-service topology and isolated data hosts specified.
- [x] Production hosts and live notification mode rejected by tests.
- [x] SHA/digest mismatch and untested/mutable image evidence rejected by tests.
- [ ] Create resources and secrets (requires explicit cost/provisioning approval).
- [ ] Build, scan and test nine exact-SHA images; populate immutable digests.
- [ ] Verify QA environment database isolation and provider SHA before any reuse.
- [ ] Deploy staging, verify runtime provenance, migration revisions and authenticated E2E.
