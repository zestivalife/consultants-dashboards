#!/usr/bin/env python3
"""Build a deterministic Railway repository-root package for Auth."""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Optional


SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SERVICE_PATH = Path("services/auth-service")
REQUIRED_FILES = (
    SERVICE_PATH / "Dockerfile",
    SERVICE_PATH / "requirements.txt",
    SERVICE_PATH / "release.sh",
    SERVICE_PATH / "app/main.py",
    SERVICE_PATH / "app/version.py",
)


def git(repository: Path, *arguments: str, text: bool = True):
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=text,
    ).stdout


def validated_head(repository: Path) -> str:
    try:
        revision = git(repository, "rev-parse", "--verify", "HEAD^{commit}").strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("Unable to establish the Git HEAD commit") from error
    if not SHA_PATTERN.fullmatch(revision):
        raise RuntimeError("Git HEAD is not an exact 40-character hexadecimal revision")
    return revision


def require_clean_checkout(repository: Path) -> None:
    status = git(repository, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError("Refusing to package a dirty Git checkout")


def extract_service(repository: Path, output: Path) -> None:
    try:
        archive = git(
            repository,
            "archive",
            "--format=tar",
            "HEAD",
            "--",
            SERVICE_PATH.as_posix(),
            text=False,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Unable to archive services/auth-service from Git HEAD") from error
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
        for member in source.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RuntimeError(f"Unsafe path in Git archive: {member.name}")
        source.extractall(output)


def write_revision(repository: Path, output: Path, revision: str) -> None:
    script = repository / "scripts/package_source_revision.sh"
    if not script.is_file():
        raise RuntimeError("Source revision packaging script is missing")
    try:
        subprocess.run([str(script), str(output)], cwd=repository, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("Source revision packaging script failed") from error
    revision_path = output / SERVICE_PATH / ".source-revision"
    if revision_path.read_text(encoding="ascii").strip() != revision:
        raise RuntimeError("Packaged source revision does not match Git HEAD")


def verify_layout(output: Path, revision: str) -> list[str]:
    missing = [path.as_posix() for path in REQUIRED_FILES if not (output / path).is_file()]
    if missing:
        raise RuntimeError(f"Package is missing required files: {', '.join(missing)}")
    packaged_revision = (output / SERVICE_PATH / ".source-revision").read_text(
        encoding="ascii"
    ).strip()
    if packaged_revision != revision:
        raise RuntimeError("Packaged source revision does not match Git HEAD")
    files = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() or path.is_symlink()
    )
    forbidden = [
        path
        for path in files
        if "/.git/" in f"/{path}/"
        or "__pycache__" in Path(path).parts
        or ".pytest_cache" in Path(path).parts
        or Path(path).name in {".env", ".env.local"}
    ]
    if forbidden:
        raise RuntimeError(f"Package contains forbidden local files: {', '.join(forbidden)}")
    return files


def deterministic_archive(output: Path, archive_path: Path) -> None:
    with archive_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in sorted(output.rglob("*")):
                    relative = path.relative_to(output).as_posix()
                    info = archive.gettarinfo(str(path), arcname=relative)
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    if path.is_file():
                        with path.open("rb") as source:
                            archive.addfile(info, source)
                    else:
                        archive.addfile(info)


def build(repository: Path, output: Path, archive_path: Optional[Path] = None) -> dict:
    repository = repository.resolve()
    output = output.resolve()
    if not (repository / SERVICE_PATH).is_dir():
        raise RuntimeError("Expected source directory is missing: services/auth-service")
    require_clean_checkout(repository)
    revision = validated_head(repository)
    if output.exists():
        if any(output.iterdir()):
            raise RuntimeError("Output directory must not already contain files")
    else:
        output.mkdir(parents=True)
    extract_service(repository, output)
    write_revision(repository, output, revision)
    files = verify_layout(output, revision)
    manifest = {"source_revision": revision, "service_root": "/services/auth-service", "files": files}
    (output / "railway-package-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if archive_path is not None:
        deterministic_archive(output, archive_path.resolve())
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    try:
        manifest = build(args.repository, args.output, args.archive)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"packaging failed: {error}\n")
    print(json.dumps({"source_revision": manifest["source_revision"], "service_root": manifest["service_root"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
