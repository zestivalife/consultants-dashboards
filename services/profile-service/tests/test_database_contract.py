from pathlib import Path

from app.config import Settings


def test_railway_postgres_url_uses_asyncpg_driver() -> None:
    settings = Settings(
        database_url="postgresql://user:password@postgres.railway.internal:5432/railway",
        redis_url="redis://redis.railway.internal:6379/0",
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_profile_service_uses_an_isolated_alembic_ledger() -> None:
    env_source = (Path(__file__).parents[1] / "alembic" / "env.py").read_text()

    assert env_source.count('version_table="profile_service_alembic_version"') == 2
