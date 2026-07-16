from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field, field_validator, model_validator
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "scoring-engine-service"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    app_port: int = Field(default=8004, validation_alias=AliasChoices("PORT", "APP_PORT", "app_port"))

    database_url: str = "postgresql+asyncpg://nuetra:nuetra_secret@localhost:5432/nuetra_scoring"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 300

    redis_url: str = "redis://localhost:6379/0"
    trusted_hosts: str = (
        "*.railway.app,*.railway.internal,scoring-engine-service,api-gateway,localhost,127.0.0.1"
    )

    profile_service_url: str = "http://profile-service:8002"
    assessment_service_url: str = "http://assessment-service:8003"

    cache_ttl_seconds: int = 600
    scoring_idempotency_minutes: int = 5
    score_version: str = "v1"
    algorithm_version: str = "2026-03"

    log_level: str = "INFO"
    log_format: str = "json"

    model_config = {"env_file": ".env", "case_sensitive": False}

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgresql+asyncpg://"):
            return value
        if value.startswith("postgresql+psycopg2://"):
            return "postgresql+asyncpg://" + value[len("postgresql+psycopg2://"):]
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value[len("postgresql://"):]
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value[len("postgres://"):]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self
        if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            raise ValueError("DATABASE_URL must be set to a production PostgreSQL connection")
        if "localhost" in self.redis_url or "127.0.0.1" in self.redis_url:
            raise ValueError("REDIS_URL must be set to a production Redis connection")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
