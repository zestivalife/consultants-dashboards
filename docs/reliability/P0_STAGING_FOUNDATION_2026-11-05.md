# P0 integrated-staging release gates

## Release boundary

- Consumer baseline: `d4c9c5ace1a8ffd8dda37fe21fc7e94db886425b`
- Provider baseline: `f7762c1eed4c3026913028742655d6c3f5a6e38e`
- Target: nine application services plus dedicated PostgreSQL and Redis.
- The checked-in manifest has `deployment_enabled: false` and no images. It is intentionally non-deployable.

## Operating-mode contracts

`CONFIG_CHECK` validates the nine-service dependency graph, dedicated data identities, staging-only environment markers, sink notifications, synthetic recipients, storage policy and release SHA syntax. Build artifacts may be absent.

`BUILD_ATTESTATION` additionally requires exactly nine registry-resolved immutable images. For every digest it independently retrieves the registry digest and OCI configuration, verifies the source-revision label, verifies a keyless Sigstore signature, verifies SLSA provenance binding the digest to source SHA/Dockerfile/context hashes, verifies a passing vulnerability-scan attestation, and retrieves successful consumer and provider CI runs from GitHub. Manifest booleans are not evidence.

`DEPLOY_GATE` includes both prior modes and additionally requires `deployment_enabled: true`, a short-lived signed authorization scoped only to `integrated-staging`, a manifest hash match, and a signed effective-runtime fingerprint snapshot. The authorization signature must originate from the protected `staging-deployment-authorize.yml` workflow on `main`; it never authorizes production.

## Trusted build and promotion mechanism

Each source repository must build its own service images from a full SHA in a manually approved `integrated-staging-build` GitHub environment. Images must use OCI revision labels and be pushed once. The workflow then obtains the registry digest, runs the security scan, emits an in-toto/SLSA statement containing `source_sha`, `dockerfile_sha256`, and `context_sha256`, and signs the image, provenance, and vulnerability result using GitHub OIDC keyless Cosign.

The gate trusts only certificates from `https://token.actions.githubusercontent.com` and the exact `staging-image-build.yml` workflow identity. Promotion uses `registry/repository@sha256:...`; rebuilding during promotion is forbidden. `crane` and `cosign` must be installed from pinned, checksum-verified releases in the gate runner.

The Fiteatsy provider must supply the same evidence from `zestivalife/Fiteatsy-mobile`; consumer CI cannot self-assert provider success. Until that workflow and its real run ID exist, `BUILD_ATTESTATION` and `DEPLOY_GATE` remain blocked.

## Effective isolation verification

`fingerprint_runtime_config.py` reads rendered runtime values directly from process environment and outputs only keyed HMAC-SHA256 fingerprints. The HMAC key is held by the protected gate environment; raw URLs, credentials and signing keys are never printed or persisted. The signed snapshot includes dedicated database/Redis resource IDs and is compared with protected production fingerprints.

Run the same `DEPLOY_GATE` twice:

1. Before deployment against the platform-rendered configuration.
2. After deployment from a restricted verification job using the actual running-service configuration.

Both invocations reject production database, Redis, service, signing-key, notification and storage fingerprints; public data targets require explicit staging resource allowlisting. Runtime acceptance is incomplete until the post-deployment check passes.

## Negative guarantees

Regression fixtures prove rejection of formatted-but-invented digests, falsified CI, disabled deployment, wrong source SHA, missing provenance, production data/service targets, production notification credentials, expired or mismatched authorization, missing images, unscanned images, real notification providers, public unallowlisted databases and shared data identities.

## Resource estimate

Proposed limits remain 0.25 vCPU/256 MiB per application, 0.5 vCPU/512 MiB PostgreSQL with 2 GB storage, and 0.25 vCPU/256 MiB Redis with 1 GB storage. At the currently documented Railway usage rates this is approximately **$90.45/month before egress and plan minimums** if continuously allocated. Sleep for stateless services should reduce usage but is not a billing guarantee.

## Provisioning readiness

- Gate implementation and negative controls: ready.
- Real build attestations and registry digests: not created; publishing requires approval.
- Provider build workflow/run: required.
- Staging resource IDs and secret-safe production fingerprint baseline: require provisioning approval.
- Signed short-lived deployment authorization: required only after artifacts and resources exist.
- Infrastructure provisioning and deployment: not performed.
