from pathlib import Path

from app import version


def test_packaged_revision_overrides_stale_environment(monkeypatch, tmp_path: Path):
    revision_file = tmp_path / ".source-revision"
    revision_file.write_text(f"{'a' * 40}\n", encoding="utf-8")
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", revision_file)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "b" * 40)

    assert version.runtime_commit_sha("c" * 40) == "a" * 40


def test_invalid_packaged_revision_falls_back_to_platform(monkeypatch, tmp_path: Path):
    revision_file = tmp_path / ".source-revision"
    revision_file.write_text("not-a-git-sha\n", encoding="utf-8")
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", revision_file)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "d" * 40)

    assert version.runtime_commit_sha("e" * 40) == "d" * 40


def test_missing_revision_uses_configured_value(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(version, "_SOURCE_REVISION_PATH", tmp_path / "missing")
    for name in ("RAILWAY_GIT_COMMIT_SHA", "GIT_COMMIT_SHA", "COMMIT_SHA"):
        monkeypatch.delenv(name, raising=False)

    assert version.runtime_commit_sha("f" * 40) == "f" * 40
