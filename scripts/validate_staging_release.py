#!/usr/bin/env python3
"""Fail-closed staging release validation with externally verified evidence."""
import argparse, base64, datetime as dt, hashlib, json, os, re, subprocess, urllib.request
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
MODES = {"CONFIG_CHECK", "BUILD_ATTESTATION", "DEPLOY_GATE"}
REQUIRED_SERVICES = {"consultant-frontend", "api-gateway", "auth-service", "profile-service", "practice-operations-service", "assessment-service", "nutrition-service", "scoring-engine-service", "fiteatsy-backend"}
TRUSTED_ISSUER = "https://token.actions.githubusercontent.com"
TRUSTED_BUILD_IDENTITY = r"^https://github.com/zestivalife/(consultants-dashboards|Fiteatsy-mobile)/.github/workflows/staging-image-build.yml@refs/heads/codex/.*$"
TRUSTED_AUTH_IDENTITY = r"^https://github.com/zestivalife/consultants-dashboards/.github/workflows/staging-deployment-authorize.yml@refs/heads/main$"

class VerificationError(RuntimeError): pass

class TrustedVerifier:
    """Retrieve evidence from GitHub/registry and cryptographically verify it."""
    def _run(self, *args):
        try: return subprocess.run(args, check=True, text=True, capture_output=True).stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as exc: raise VerificationError(f"trusted verification command failed: {args[0]}") from exc
    def ci_run(self, repository, run_id):
        headers = {"Accept": "application/vnd.github+json"}
        if os.environ.get("GITHUB_TOKEN"): headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
        req = urllib.request.Request(f"https://api.github.com/repos/{repository}/actions/runs/{run_id}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response: return json.load(response)
        except Exception as exc: raise VerificationError("GitHub CI evidence could not be independently retrieved") from exc
    def registry_digest(self, image): return self._run("crane", "digest", image).strip()
    def image_config(self, image): return json.loads(self._run("crane", "config", image))
    def verify_image_signature(self, image):
        self._run("cosign", "verify", image, "--certificate-identity-regexp", TRUSTED_BUILD_IDENTITY, "--certificate-oidc-issuer", TRUSTED_ISSUER); return True
    def verify_attestation(self, image, kind):
        output = self._run("cosign", "verify-attestation", image, "--type", kind, "--certificate-identity-regexp", TRUSTED_BUILD_IDENTITY, "--certificate-oidc-issuer", TRUSTED_ISSUER)
        envelopes = [json.loads(line) for line in output.splitlines() if line.strip()]
        records = []
        for envelope in envelopes:
            try: records.append(json.loads(base64.b64decode(envelope["payload"])))
            except (KeyError, ValueError, json.JSONDecodeError) as exc: raise VerificationError(f"malformed trusted {kind} attestation") from exc
        if not records: raise VerificationError(f"missing trusted {kind} attestation")
        return records
    def verify_blob(self, path, signature, identity):
        self._run("cosign", "verify-blob", path, "--signature", signature, "--certificate", f"{signature}.pem", "--certificate-identity-regexp", identity, "--certificate-oidc-issuer", TRUSTED_ISSUER)
        return json.loads(Path(path).read_text())

def canonical_sha256(value): return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def config_errors(topology, manifest, runtime=None):
    errors = []
    if topology.get("environment") != "integrated-staging" or topology.get("production_access") is not False: errors.append("topology is not isolated integrated-staging")
    if set(topology.get("services", {})) != REQUIRED_SERVICES: errors.append("topology must contain exactly nine required services")
    data = topology.get("data_services", {})
    if set(data) != {"postgres", "redis"}: errors.append("dedicated PostgreSQL and Redis are required")
    identities = [x.get("resource_id") for x in data.values()]
    if any(not x for x in identities) or len(set(identities)) != len(identities): errors.append("missing or shared database identities")
    for name, entry in data.items():
        if entry.get("environment") != "integrated-staging" or entry.get("shared_with_production") is not False: errors.append(f"{name} is not isolated from production")
        if entry.get("public") and entry.get("resource_id") not in topology.get("allowed_public_staging_resources", []): errors.append(f"{name} public target is not allowlisted")
    notifications = topology.get("notifications", {})
    if notifications.get("mode") != "sink" or notifications.get("provider") != "local-sink": errors.append("real notification providers are forbidden")
    if notifications.get("recipient_domains") != ["example.test"]: errors.append("notification recipients are not synthetic")
    if topology.get("storage", {}).get("provider") not in {"local", "staging-isolated"}: errors.append("unexpected external storage destination")
    for name, service in topology.get("services", {}).items():
        if service.get("environment") != "integrated-staging": errors.append(f"{name}: wrong environment")
        if set(service.get("dependencies", [])) - (REQUIRED_SERVICES | {"postgres", "redis"}): errors.append(f"{name}: unknown dependency")
    if manifest.get("environment") != "integrated-staging": errors.append("manifest environment mismatch")
    for key in ("consumer_sha", "provider_sha"):
        if not SHA.fullmatch(manifest.get(key, "")): errors.append(f"invalid {key}")
    if runtime:
        production = set(runtime.get("production_fingerprints", [])); effective = runtime.get("effective", {})
        required = {"database", "redis", "signing_key", "service_endpoints", "storage", "notifications"}
        if set(effective) != required: errors.append("effective runtime configuration is incomplete")
        for category, values in effective.items():
            values = values if isinstance(values, list) else [values]
            if any(not isinstance(v, str) or not DIGEST.fullmatch(v) for v in values): errors.append(f"{category}: invalid secret-safe fingerprint")
            if production.intersection(values): errors.append(f"{category}: production target or credential detected")
        if runtime.get("database_identity") != data.get("postgres", {}).get("resource_id"): errors.append("effective database identity mismatch")
        if runtime.get("redis_identity") != data.get("redis", {}).get("resource_id"): errors.append("effective Redis identity mismatch")
    return errors

def attestation_errors(manifest, verifier):
    errors = []; images = manifest.get("images", [])
    if {x.get("service") for x in images} != REQUIRED_SERVICES or len(images) != len(REQUIRED_SERVICES): return ["verified images are required exactly once for all nine services"]
    for item in images:
        service = item.get("service", "unknown"); expected = manifest["provider_sha"] if service == "fiteatsy-backend" else manifest["consumer_sha"]
        digest = item.get("digest", ""); immutable = item.get("registry_reference", "")
        repository = immutable.rsplit("@", 1)[0] if "@" in immutable else immutable
        if not DIGEST.fullmatch(digest) or immutable != f"{repository}@{digest}" or ":" in repository.rsplit("/", 1)[-1]: errors.append(f"{service}: invalid or mutable image reference"); continue
        if item.get("source_sha") != expected: errors.append(f"{service}: wrong source SHA")
        if not DIGEST.fullmatch(item.get("dockerfile_sha256", "")) or not DIGEST.fullmatch(item.get("context_sha256", "")): errors.append(f"{service}: missing build-context provenance")
        try:
            if verifier.registry_digest(immutable) != digest: errors.append(f"{service}: invented or stale registry digest")
            labels = verifier.image_config(immutable).get("config", {}).get("Labels", {}) or {}
            if labels.get("org.opencontainers.image.revision") != expected: errors.append(f"{service}: OCI source revision mismatch")
            verifier.verify_image_signature(immutable)
            provenance = verifier.verify_attestation(immutable, "slsaprovenance")
            scans = verifier.verify_attestation(immutable, "vuln")
            tests = verifier.verify_attestation(immutable, "https://zestivalife.dev/attestations/test/v1")
            def subject_matches(record):
                return any(x.get("digest", {}).get("sha256") == digest.removeprefix("sha256:") for x in record.get("subject", []))
            def build_matches(record):
                params = record.get("predicate", {}).get("buildDefinition", {}).get("externalParameters", {})
                return subject_matches(record) and params.get("source_sha") == expected and params.get("dockerfile_sha256") == item.get("dockerfile_sha256") and params.get("context_sha256") == item.get("context_sha256")
            if not any(build_matches(x) for x in provenance): errors.append(f"{service}: missing or mismatched image provenance")
            if not any(subject_matches(x) and x.get("predicate", {}).get("result") == "pass" for x in scans): errors.append(f"{service}: image is unscanned or scan did not pass")
            if not any(subject_matches(x) and x.get("predicate", {}).get("result") == "pass" for x in tests): errors.append(f"{service}: exact image is untested or tests did not pass")
        except VerificationError as exc: errors.append(f"{service}: {exc}")
    expected_ci = {"consumer": manifest.get("consumer_sha"), "provider": manifest.get("provider_sha")}
    ci_entries = manifest.get("ci", [])
    if {x.get("role") for x in ci_entries} != set(expected_ci): errors.append("consumer and provider CI evidence are both required")
    for ci in ci_entries:
        try:
            run = verifier.ci_run(ci.get("repository", ""), ci.get("run_id"))
            if run.get("head_sha") != expected_ci.get(ci.get("role")) or run.get("status") != "completed" or run.get("conclusion") != "success": errors.append(f"trusted {ci.get('role')} CI result is falsified or mismatched")
        except VerificationError as exc: errors.append(str(exc))
    return errors

def validate(mode, topology, manifest, runtime=None, verifier=None, authorization=None, now=None):
    if mode not in MODES: return ["unknown validation mode"]
    errors = config_errors(topology, manifest, runtime)
    if mode == "CONFIG_CHECK": return errors
    verifier = verifier or TrustedVerifier(); errors.extend(attestation_errors(manifest, verifier))
    if mode == "BUILD_ATTESTATION": return errors
    if manifest.get("deployment_enabled") is not True: errors.append("deployment_enabled=false blocks deployment")
    if not runtime: errors.append("signed effective runtime evidence is required")
    if not authorization: errors.append("signed staging deployment authorization is required")
    else:
        current = now or dt.datetime.now(dt.timezone.utc)
        try: expires = dt.datetime.fromisoformat(authorization.get("expires_at", "").replace("Z", "+00:00"))
        except ValueError: expires = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        if authorization.get("scope") != "integrated-staging" or authorization.get("production_authorized") is not False: errors.append("authorization is not staging-only")
        if authorization.get("manifest_sha256") != canonical_sha256(manifest): errors.append("authorization manifest mismatch")
        if expires <= current: errors.append("deployment authorization is expired")
    return errors

def main():
    p = argparse.ArgumentParser(); p.add_argument("--mode", choices=sorted(MODES), required=True); p.add_argument("--topology", default="deploy/staging/topology.json"); p.add_argument("--manifest", default="deploy/staging/release-manifest.json"); p.add_argument("--runtime"); p.add_argument("--authorization"); p.add_argument("--authorization-signature"); p.add_argument("--runtime-signature"); args = p.parse_args()
    topology = json.loads(Path(args.topology).read_text()); manifest = json.loads(Path(args.manifest).read_text()); runtime = json.loads(Path(args.runtime).read_text()) if args.runtime else None; verifier = TrustedVerifier(); authorization = None
    if args.mode == "DEPLOY_GATE" and args.authorization and args.authorization_signature:
        try:
            authorization = verifier.verify_blob(args.authorization, args.authorization_signature, TRUSTED_AUTH_IDENTITY)
            if not runtime or not args.runtime_signature: raise VerificationError("signed runtime evidence is required")
            verifier.verify_blob(args.runtime, args.runtime_signature, TRUSTED_BUILD_IDENTITY)
        except VerificationError as exc: print(f"ERROR: {exc}"); return 1
    errors = validate(args.mode, topology, manifest, runtime, verifier, authorization)
    if errors: print("\n".join(f"ERROR: {x}" for x in errors)); return 1
    print(f"{args.mode} passed"); return 0

if __name__ == "__main__": raise SystemExit(main())
