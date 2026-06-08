from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "profile-service"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    app_port: int = 8002

    database_url: str = "postgresql+asyncpg://nuetra:nuetra_secret@localhost:5432/nuetra_profile"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 300

    redis_url: str = "redis://localhost:6379/0"

    log_level: str = "INFO"
    log_format: str = "json"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
