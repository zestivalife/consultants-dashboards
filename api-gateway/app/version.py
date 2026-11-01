from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path


_STARTED_AT = datetime.now(UTC).isoformat()
_SOURCE_REVISION_PATH = Path(__file__).resolve().parents[1] / ".source-revision"
_GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _first_env(*names: str, default: str = "unknown") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _packaged_source_revision() -> str | None:
    try:
        revision = _SOURCE_REVISION_PATH.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return None
    return revision if _GIT_SHA_PATTERN.fullmatch(revision) else None


def get_runtime_version(service: str, app_version: str, environment: str) -> dict[str, str]:
    build_time = _first_env("BUILD_TIMESTAMP", "RAILWAY_DEPLOYMENT_CREATED_AT", default=_STARTED_AT)
    return {
        "service": service,
        "version": app_version,
        "app_version": app_version,
        "environment": environment,
        "commit_sha": _packaged_source_revision()
        or _first_env("RAILWAY_GIT_COMMIT_SHA", "GIT_COMMIT_SHA", "COMMIT_SHA", "VERCEL_GIT_COMMIT_SHA"),
        "branch": _first_env("RAILWAY_GIT_BRANCH", "VERCEL_GIT_COMMIT_REF", "GIT_BRANCH", "BRANCH"),
        "build_time": build_time,
        "build_timestamp": build_time,
        "migration_version": _first_env("MIGRATION_VERSION", "ALEMBIC_VERSION"),
        "runtime_started_at": _STARTED_AT,
        "deployment_id": _first_env("RAILWAY_DEPLOYMENT_ID", "VERCEL_DEPLOYMENT_ID", "DEPLOYMENT_ID"),
        "image_digest": _first_env("DOCKER_IMAGE_DIGEST", "RAILWAY_DOCKER_IMAGE_DIGEST", "IMAGE_DIGEST"),
        "service_name": _first_env("RAILWAY_SERVICE_NAME", default=service),
        "runtime": "railway",
    }
