from app.version import get_runtime_version


def test_explicit_release_identity_wins_over_stale_provider_metadata(monkeypatch):
    monkeypatch.setenv("RELEASE_GIT_COMMIT_SHA", "release-sha")
    monkeypatch.setenv("RELEASE_GIT_BRANCH", "release-branch")
    monkeypatch.setenv("COMMIT_SHA", "stale-sha")
    monkeypatch.setenv("RAILWAY_GIT_BRANCH", "stale-branch")

    version = get_runtime_version("gateway", "1.0.0", "production")

    assert version["commit_sha"] == "release-sha"
    assert version["branch"] == "release-branch"
