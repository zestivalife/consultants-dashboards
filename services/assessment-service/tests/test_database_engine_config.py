from types import SimpleNamespace

from app.db import session


def test_database_engine_uses_configured_pool_timeout(monkeypatch):
    captured = {}
    fake_engine = object()
    settings = SimpleNamespace(
        database_url="postgresql+asyncpg://example.invalid/test",
        db_pool_size=20,
        db_max_overflow=10,
        db_pool_recycle=300,
        db_pool_timeout=30,
        app_name="assessment-service",
        app_debug=False,
    )

    monkeypatch.setattr(session, "_engine", None)
    monkeypatch.setattr(session, "get_settings", lambda: settings)

    def fake_create_async_engine(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return fake_engine

    monkeypatch.setattr(session, "create_async_engine", fake_create_async_engine)

    assert session.get_engine() is fake_engine
    assert captured["pool_timeout"] == 30
