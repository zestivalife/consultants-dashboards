#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICES = [
    ROOT / "api-gateway",
    ROOT / "services" / "auth-service",
    ROOT / "services" / "profile-service",
    ROOT / "services" / "assessment-service",
    ROOT / "services" / "scoring-engine-service",
    ROOT / "services" / "nutrition-service",
]


def file_contains(path: Path, needle: str) -> bool:
    return needle in path.read_text()


def main() -> int:
    failures: list[str] = []

    for service_dir in SERVICES:
        dockerfile = service_dir / "Dockerfile"
        if not dockerfile.exists():
            failures.append(f"{service_dir.name}: missing Dockerfile")
            continue

        docker_text = dockerfile.read_text()
        if "${PORT:-" not in docker_text:
            failures.append(f"{service_dir.name}: Dockerfile does not bind to PORT")

        if service_dir.name != "api-gateway":
            release_script = service_dir / "release.sh"
            if not release_script.exists():
                failures.append(f"{service_dir.name}: missing release.sh")

        main_py = service_dir / "app" / "main.py"
        if not main_py.exists():
            failures.append(f"{service_dir.name}: missing main.py")
        elif not file_contains(main_py, "TrustedHostMiddleware"):
            failures.append(f"{service_dir.name}: missing TrustedHostMiddleware")

        health_py = service_dir / "app" / "api" / "v1" / "routes" / "health.py"
        if service_dir.name == "api-gateway":
            health_py = service_dir / "app" / "main.py"
        if not health_py.exists():
            failures.append(f"{service_dir.name}: missing health endpoint source")
        elif not file_contains(health_py, "/ready") and service_dir.name == "api-gateway":
            failures.append(f"{service_dir.name}: missing ready endpoint")

    if failures:
        print("Deployment verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Deployment verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
