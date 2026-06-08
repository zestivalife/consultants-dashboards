from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "nutrition-service"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    app_port: int = 8005

    database_url: str = "postgresql+asyncpg://nuetra:nuetra_secret@localhost:5432/nuetra_nutrition"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 300

    redis_url: str = "redis://localhost:6379/0"

    upload_backend: str = "local"
    upload_local_dir: str = "uploads"
    s3_bucket: str = ""
    s3_region: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_endpoint_url: str = ""

    log_level: str = "INFO"
    log_format: str = "json"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
