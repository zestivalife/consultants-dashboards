#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import which


ROOT = Path(__file__).resolve().parents[1]
SERVICE_DIRS = [
    ROOT / "services" / "auth-service",
    ROOT / "services" / "profile-service",
    ROOT / "services" / "assessment-service",
    ROOT / "services" / "scoring-engine-service",
    ROOT / "services" / "nutrition-service",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )


def main() -> int:
    failures: list[str] = []

    if which("alembic") is None:
        print("alembic is not installed in the current shell; static migration files were detected but live migration checks were skipped.")
        for service_dir in SERVICE_DIRS:
            versions_dir = service_dir / "alembic" / "versions"
            release_script = service_dir / "release.sh"
            print(f"=== {service_dir.name} ===")
            print(f"versions: {'present' if versions_dir.exists() and any(versions_dir.iterdir()) else 'missing'}")
            print(f"release.sh: {'present' if release_script.exists() else 'missing'}")
            if not versions_dir.exists() or not any(versions_dir.iterdir()):
                failures.append(f"{service_dir.name}: missing migration files")
            if not release_script.exists():
                failures.append(f"{service_dir.name}: missing release.sh")
        return 1 if failures else 0

    for service_dir in SERVICE_DIRS:
        service_name = service_dir.name
        versions_dir = service_dir / "alembic" / "versions"
        release_script = service_dir / "release.sh"

        if not versions_dir.exists() or not any(versions_dir.iterdir()):
            failures.append(f"{service_name}: missing migration files")
            continue

        if not release_script.exists():
            failures.append(f"{service_name}: missing release.sh")

        current = run(["alembic", "current"], service_dir)
        heads = run(["alembic", "heads"], service_dir)

        print(f"=== {service_name} ===")
        print(current.stdout.strip() or current.stderr.strip() or "(no current output)")
        print(heads.stdout.strip() or heads.stderr.strip() or "(no heads output)")

        if current.returncode != 0:
            failures.append(f"{service_name}: alembic current failed")
        if heads.returncode != 0:
            failures.append(f"{service_name}: alembic heads failed")

    if failures:
        print("\nMigration verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nMigration verification completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
