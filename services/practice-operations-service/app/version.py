from __future__ import annotations

import os
import re
from pathlib import Path


_SOURCE_REVISION_PATH = Path(__file__).resolve().parents[1] / ".source-revision"
_GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _packaged_source_revision() -> str | None:
    try:
        revision = _SOURCE_REVISION_PATH.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return None
    return revision if _GIT_SHA_PATTERN.fullmatch(revision) else None


def runtime_commit_sha(configured_revision: str) -> str:
    return _packaged_source_revision() or next(
        (
            value
            for name in (
                "RAILWAY_GIT_COMMIT_SHA",
                "GIT_COMMIT_SHA",
                "COMMIT_SHA",
            )
            if (value := os.getenv(name))
        ),
        configured_revision,
    )
