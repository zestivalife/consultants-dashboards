from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "auth-service"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.1"
    app_port: int = Field(default=8001, validation_alias=AliasChoices("PORT", "APP_PORT", "app_port"))
    frontend_url: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://nuetra:nuetra_secret@localhost:5432/nuetra_auth"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 300
    db_pool_timeout: int = 30

    redis_url: str = "redis://localhost:6379/0"
    trusted_hosts: str = (
        "*.railway.app,*.railway.internal,auth-service.railway.internal,auth-service,api-gateway,localhost,127.0.0.1"
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expiry_minutes: int = 15
    jwt_refresh_expiry_days: int = 7

    max_failed_login_attempts: int = 5
    account_lock_minutes: int = 15
    otp_expiry_seconds: int = 300

    # SMTP / Email (fallback when EMAIL_PROVIDER=smtp)
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = "apikey"
    smtp_password: str = ""          # set via SMTP_PASSWORD env var
    smtp_from_email: str = "admin@nuetra.in"
    smtp_from_name: str = "Nuetra"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    # SendGrid REST API (set via SENDGRID_API_KEY env var — never hardcode)
    sendgrid_api_key: str | None = None

    # Email provider: "sendgrid" | "smtp" | "auto"
    # sendgrid = always use SendGrid REST API (recommended; avoids SMTP port blocking)
    # smtp     = always use SMTP
    # auto     = SendGrid if SENDGRID_API_KEY is present, else SMTP
    email_provider: str = "sendgrid"

    # Rate limiting
    login_rate_limit_max: int = 10
    login_rate_limit_window_seconds: int = 60

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
        if self.app_env.lower() == "production" and self.jwt_secret_key == "change-me-in-production":
            raise ValueError("JWT_SECRET_KEY must be set in production")
        if self.app_env.lower() == "production" and self.frontend_url.startswith(("http://localhost", "http://127.0.0.1")):
            self.frontend_url = "https://consultant.nuetra.in"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
