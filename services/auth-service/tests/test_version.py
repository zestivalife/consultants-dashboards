from pathlib import Path

from app import version


def test_packaged_revision_overrides_stale_environment(monkeypatch, tmp_path: Path):
    revision = "a" * 40
    revision_file = tmp_path / ".source-revision"
    revision_file.write_text(f"{revision}\n", encoding="utf-8")
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", revision_file)
    monkeypatch.setenv("COMMIT_SHA", "b" * 40)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "c" * 40)

    runtime = version.get_runtime_version("auth-service", "1", "test")

    assert runtime["commit_sha"] == revision


def test_platform_revision_precedes_generic_environment(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", tmp_path / "missing")
    monkeypatch.setenv("COMMIT_SHA", "b" * 40)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "c" * 40)

    runtime = version.get_runtime_version("auth-service", "1", "test")

    assert runtime["commit_sha"] == "c" * 40


def test_invalid_packaged_revision_is_not_reported(monkeypatch, tmp_path: Path):
    revision_file = tmp_path / ".source-revision"
    revision_file.write_text("not-a-git-sha\n", encoding="utf-8")
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", revision_file)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "d" * 40)

    runtime = version.get_runtime_version("auth-service", "1", "test")

    assert runtime["commit_sha"] == "d" * 40
