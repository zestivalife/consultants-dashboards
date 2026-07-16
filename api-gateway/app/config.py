from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


DEFAULT_CORS_ORIGINS = [
    "https://consultant.nuetra.in",
    "https://consultants-dashboards.vercel.app",
    "https://nuetra.in",
    "https://www.nuetra.in",
    "http://localhost:3000",
]


class ServiceRoute(BaseSettings):
    prefix: str
    upstream: str


class Settings(BaseSettings):
    app_name: str = "nuetra-api-gateway"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    app_port: int = Field(default=8000, validation_alias=AliasChoices("PORT", "APP_PORT", "app_port"))

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    redis_url: str = Field(
        default="redis://redis:6379/1",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )

    rate_limit_per_minute: int = 60

    cors_origins: list[str] = Field(
        default_factory=lambda: DEFAULT_CORS_ORIGINS.copy(),
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    trusted_hosts: str = (
        "api.nuetra.in,*.railway.app,*.railway.internal,api-gateway,localhost,127.0.0.1"
    )

    log_level: str = "INFO"
    log_format: str = "json"

    auth_service_url: str = "http://auth-service:8001"
    profile_service_url: str = "http://profile-service:8002"
    assessment_service_url: str = "http://assessment-service:8003"
    scoring_service_url: str = "http://scoring-engine-service:8004"
    nutrition_service_url: str = "http://nutrition-service:8005"

    model_config = {"env_file": ".env", "case_sensitive": False}

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.lower() == "production" and self.jwt_secret_key == "change-me-in-production":
            raise ValueError("JWT_SECRET_KEY must be set in production")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return DEFAULT_CORS_ORIGINS.copy()
        if isinstance(value, list):
            return [origin.strip() for origin in value if isinstance(origin, str) and origin.strip()]
        if isinstance(value, str):
            parsed = [origin.strip() for origin in value.split(",") if origin.strip()]
            return parsed or DEFAULT_CORS_ORIGINS.copy()
        raise TypeError("cors_origins must be a comma-separated string or list of strings")

    @staticmethod
    def _normalize_service_url(url: str, default_port: int) -> str:
        parsed = urlsplit(url.strip().rstrip("/"))
        if parsed.scheme not in {"http", "https"}:
            return url.strip().rstrip("/")
        if parsed.port is not None:
            return url.strip().rstrip("/")
        if not parsed.hostname or not parsed.hostname.endswith(".railway.internal"):
            return url.strip().rstrip("/")

        netloc = f"{parsed.hostname}:{default_port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path.rstrip("/"), "", ""))

    def get_service_upstreams(self) -> dict[str, str]:
        return {
            "auth-service": self._normalize_service_url(self.auth_service_url, 8001),
            "profile-service": self._normalize_service_url(self.profile_service_url, 8002),
            "assessment-service": self._normalize_service_url(self.assessment_service_url, 8003),
            "scoring-engine-service": self._normalize_service_url(self.scoring_service_url, 8004),
            "nutrition-service": self._normalize_service_url(self.nutrition_service_url, 8005),
        }

    def get_service_routes(self) -> list[dict]:
        upstreams = self.get_service_upstreams()
        auth_service_url = upstreams["auth-service"]
        profile_service_url = upstreams["profile-service"]
        assessment_service_url = upstreams["assessment-service"]
        scoring_service_url = upstreams["scoring-engine-service"]
        nutrition_service_url = upstreams["nutrition-service"]

        return [
            {"prefix": "/api/v1/corporate-admin", "upstream": auth_service_url},
            {"prefix": "/api/v1/owner/people-access", "upstream": auth_service_url},
            {"prefix": "/api/v1/owner/master-data", "upstream": auth_service_url},
            {"prefix": "/api/v1/team-lead", "upstream": auth_service_url},
            {"prefix": "/api/v1/team-member", "upstream": auth_service_url},
            {"prefix": "/api/v1/notifications", "upstream": auth_service_url},
            {"prefix": "/api/v1/auth", "upstream": auth_service_url},
            {"prefix": "/api/v1/profile", "upstream": profile_service_url},
            {"prefix": "/api/v1/assessments", "upstream": assessment_service_url},
            {"prefix": "/api/v1/scoring", "upstream": scoring_service_url},
            {"prefix": "/api/v1/nutrition", "upstream": nutrition_service_url},
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
