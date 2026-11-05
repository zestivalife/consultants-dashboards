#!/usr/bin/env python3
"""Fail-closed validation for immutable integrated-staging releases."""

import argparse
import json
import re
import socket
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED_SERVICES = {
    "consultant-frontend", "api-gateway", "auth-service", "profile-service",
    "practice-operations-service", "assessment-service", "nutrition-service",
    "scoring-engine-service", "fiteatsy-backend",
}


def validate(topology, manifest, require_images=True):
    errors = []
    if topology.get("environment") != "integrated-staging" or topology.get("production_access") is not False:
        errors.append("topology must be isolated integrated-staging with production_access=false")
    if set(topology.get("services", [])) != REQUIRED_SERVICES:
        errors.append("topology must contain exactly the nine required application services")
    safety = topology.get("safety", {})
    if safety.get("notification_mode") != "sink":
        errors.append("external notifications must use sink mode")
    for name, data in topology.get("data_services", {}).items():
        host = data.get("host", "").lower()
        database = data.get("database", "staging")
        if "staging" not in host or "prod" in host or "production" in host:
            errors.append(f"{name} host is not staging-isolated")
        if name == "postgres" and "staging" not in database.lower():
            errors.append("PostgreSQL database name must identify staging")
    if manifest.get("environment") != "integrated-staging":
        errors.append("manifest environment mismatch")
    for key in ("consumer_sha", "provider_sha"):
        if not SHA.fullmatch(manifest.get(key, "")):
            errors.append(f"invalid {key}")
    if manifest.get("ci", {}).get("conclusion") != "success":
        errors.append("exact-SHA CI is not successful")
    images = manifest.get("images", [])
    if require_images and {item.get("service") for item in images} != REQUIRED_SERVICES:
        errors.append("tested immutable images are required for all nine services")
    for item in images:
        expected = manifest["provider_sha"] if item.get("service") == "fiteatsy-backend" else manifest["consumer_sha"]
        if item.get("source_sha") != expected:
            errors.append(f"{item.get('service')}: source SHA does not match release baseline")
        if not DIGEST.fullmatch(item.get("digest", "")):
            errors.append(f"{item.get('service')}: invalid immutable digest")
        if item.get("tested") is not True:
            errors.append(f"{item.get('service')}: image has not passed tests")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topology", default="deploy/staging/topology.json")
    parser.add_argument("--manifest", default="deploy/staging/release-manifest.json")
    parser.add_argument("--allow-build-pending", action="store_true")
    parser.add_argument("--check-no-production-dns", action="store_true")
    args = parser.parse_args()
    topology = json.loads(Path(args.topology).read_text())
    manifest = json.loads(Path(args.manifest).read_text())
    errors = validate(topology, manifest, not args.allow_build_pending)
    if args.check_no_production_dns:
        for data in topology["data_services"].values():
            try:
                socket.getaddrinfo(data["host"], None)
                errors.append(f"staging placeholder unexpectedly resolves: {data['host']}")
            except socket.gaierror:
                pass
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("staging release configuration is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
