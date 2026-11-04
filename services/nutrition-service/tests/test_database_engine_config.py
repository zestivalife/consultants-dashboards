from app.config import Settings


def test_database_pool_timeout_is_available_to_engine_configuration() -> None:
    settings = Settings()

    assert settings.db_pool_timeout == 30
