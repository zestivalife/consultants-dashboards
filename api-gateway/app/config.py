from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class ServiceRoute(BaseSettings):
    prefix: str
    upstream: str


class Settings(BaseSettings):
    app_name: str = "nuetra-api-gateway"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    redis_url: str = "redis://localhost:6379/1"

    rate_limit_per_minute: int = 60

    cors_origins: str = "http://localhost:3000,https://nuetra.in,https://www.nuetra.in"

    log_level: str = "INFO"
    log_format: str = "json"

    auth_service_url: str = "http://auth-service:8001"
    profile_service_url: str = "http://profile-service:8002"
    assessment_service_url: str = "http://assessment-service:8003"
    scoring_service_url: str = "http://scoring-engine-service:8004"
    nutrition_service_url: str = "http://nutrition-service:8005"
    consultation_service_url: str = "http://consultation-service:8006"
    pathology_service_url: str = "http://pathology-service:8007"
    wearable_service_url: str = "http://wearable-service:8008"
    analytics_service_url: str = "http://analytics-service:8009"
    admin_service_url: str = "http://admin-service:8010"
    notification_service_url: str = "http://notification-service:8011"
    payment_service_url: str = "http://payment-service:8012"

    model_config = {"env_file": ".env", "case_sensitive": False}

    def get_service_routes(self) -> list[dict]:
        return [
            {"prefix": "/api/v1/corporate-admin", "upstream": self.auth_service_url},
            {"prefix": "/api/v1/team-lead", "upstream": self.auth_service_url},
            {"prefix": "/api/v1/team-member", "upstream": self.auth_service_url},
            {"prefix": "/api/v1/notifications", "upstream": self.auth_service_url},
            {"prefix": "/api/v1/auth", "upstream": self.auth_service_url},
            {"prefix": "/api/v1/profile", "upstream": self.profile_service_url},
            {"prefix": "/api/v1/assessments", "upstream": self.assessment_service_url},
            {"prefix": "/api/v1/scoring", "upstream": self.scoring_service_url},
            {"prefix": "/api/v1/nutrition", "upstream": self.nutrition_service_url},
            {"prefix": "/api/v1/consultations", "upstream": self.consultation_service_url},
            {"prefix": "/api/v1/pathology", "upstream": self.pathology_service_url},
            {"prefix": "/api/v1/wearables", "upstream": self.wearable_service_url},
            {"prefix": "/api/v1/analytics", "upstream": self.analytics_service_url},
            {"prefix": "/api/v1/admin", "upstream": self.admin_service_url},
            {"prefix": "/api/v1/payments", "upstream": self.payment_service_url},
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
