from pathlib import Path

from app import version


def test_packaged_revision_overrides_stale_environment(monkeypatch, tmp_path: Path):
    revision_file = tmp_path / ".source-revision"
    revision_file.write_text(f"{'a' * 40}\n", encoding="utf-8")
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", revision_file)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "b" * 40)

    runtime = version.get_runtime_version("api-gateway", "1", "test")

    assert runtime["commit_sha"] == "a" * 40


def test_invalid_packaged_revision_uses_platform_revision(monkeypatch, tmp_path: Path):
    revision_file = tmp_path / ".source-revision"
    revision_file.write_text("not-a-git-sha\n", encoding="utf-8")
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", revision_file)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "c" * 40)

    runtime = version.get_runtime_version("api-gateway", "1", "test")

    assert runtime["commit_sha"] == "c" * 40
