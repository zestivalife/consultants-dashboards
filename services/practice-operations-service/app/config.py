from functools import lru_cache
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings

from app.fiteatsy_assertions import parse_public_keyring


class Settings(BaseSettings):
    app_name: str = "practice-operations-service"
    app_env: str = "development"
    app_version: str = "0.1.0"
    app_commit_sha: str = Field(default="unknown", validation_alias=AliasChoices("APP_COMMIT_SHA", "RAILWAY_GIT_COMMIT_SHA"))
    app_port: int = Field(default=8006, validation_alias=AliasChoices("PORT", "APP_PORT"))
    auth_service_url: str = Field(default="http://auth-service:8001", validation_alias=AliasChoices("AUTH_SERVICE_URL", "auth_service_url"))
    database_url: str = "postgresql+asyncpg://nuetra:nuetra_secret@localhost:5432/nuetra_practice_operations"
    trusted_hosts: str = "*.railway.app,*.railway.internal,practice-operations-service,api-gateway,localhost,127.0.0.1"
    profession_intake_secret: str = Field(default="development-profession-intake-secret", validation_alias=AliasChoices("PROFESSION_INTAKE_SECRET", "profession_intake_secret"))
    profession_intake_public_url: str = Field(default="http://localhost:3000/profession-intake", validation_alias=AliasChoices("PROFESSION_INTAKE_PUBLIC_URL", "profession_intake_public_url"))
    client_portal_secret: str = Field(default="development-client-portal-secret", validation_alias=AliasChoices("CLIENT_PORTAL_SECRET", "client_portal_secret"))
    client_portal_public_url: str = Field(default="http://localhost:3000/client-portal", validation_alias=AliasChoices("CLIENT_PORTAL_PUBLIC_URL", "client_portal_public_url"))
    private_notes_encryption_key: str = Field(default="development-private-notes-key", validation_alias=AliasChoices("PRIVATE_NOTES_ENCRYPTION_KEY", "private_notes_encryption_key"))
    qa_delegation_public_key: str | None = Field(default=None, validation_alias=AliasChoices("QA_DELEGATION_PUBLIC_KEY", "qa_delegation_public_key"))
    qa_delegation_issuer: str = Field(default="consultant-auth-service", validation_alias=AliasChoices("QA_DELEGATION_ISSUER", "qa_delegation_issuer"))
    qa_delegation_audience: str = Field(default="practice-operations-service", validation_alias=AliasChoices("QA_DELEGATION_AUDIENCE", "qa_delegation_audience"))
    document_storage_bucket: str | None = Field(default=None, validation_alias=AliasChoices("DOCUMENT_STORAGE_BUCKET","document_storage_bucket"))
    document_storage_region: str = Field(default="ap-south-1", validation_alias=AliasChoices("DOCUMENT_STORAGE_REGION","document_storage_region"))
    document_storage_endpoint: str | None = Field(default=None, validation_alias=AliasChoices("DOCUMENT_STORAGE_ENDPOINT","document_storage_endpoint"))
    document_storage_access_key: str | None = Field(default=None, validation_alias=AliasChoices("DOCUMENT_STORAGE_ACCESS_KEY","document_storage_access_key"))
    document_storage_secret_key: str | None = Field(default=None, validation_alias=AliasChoices("DOCUMENT_STORAGE_SECRET_KEY","document_storage_secret_key"))
    payment_provider: str | None = Field(default=None, validation_alias=AliasChoices("PAYMENT_PROVIDER","payment_provider"))
    razorpay_key_id: str | None = Field(default=None, validation_alias=AliasChoices("RAZORPAY_KEY_ID","razorpay_key_id"))
    razorpay_key_secret: str | None = Field(default=None, validation_alias=AliasChoices("RAZORPAY_KEY_SECRET","razorpay_key_secret"))
    razorpay_webhook_secret: str | None = Field(default=None, validation_alias=AliasChoices("RAZORPAY_WEBHOOK_SECRET","razorpay_webhook_secret"))
    ai_runtime_provider: str | None = Field(default=None, validation_alias=AliasChoices("AI_RUNTIME_PROVIDER","ai_runtime_provider"))
    external_fiteatsy_connection_enabled: bool = Field(default=False, validation_alias=AliasChoices("EXTERNAL_FITEATSY_CONNECTION_ENABLED", "external_fiteatsy_connection_enabled"))
    external_fiteatsy_health_access_enabled: bool = Field(default=False, validation_alias=AliasChoices("EXTERNAL_FITEATSY_HEALTH_ACCESS_ENABLED", "external_fiteatsy_health_access_enabled"))
    external_fiteatsy_diet_publish_enabled: bool = Field(default=False, validation_alias=AliasChoices("EXTERNAL_FITEATSY_DIET_PUBLISH_ENABLED", "external_fiteatsy_diet_publish_enabled"))
    external_fiteatsy_scheduling_enabled: bool = Field(default=False, validation_alias=AliasChoices("EXTERNAL_FITEATSY_SCHEDULING_ENABLED", "external_fiteatsy_scheduling_enabled"))
    external_fiteatsy_pin_pepper: str | None = Field(default=None, validation_alias=AliasChoices("EXTERNAL_FITEATSY_PIN_PEPPER", "external_fiteatsy_pin_pepper"))
    external_fiteatsy_inbound_public_key: str | None = Field(default=None, validation_alias=AliasChoices("EXTERNAL_FITEATSY_INBOUND_PUBLIC_KEY", "external_fiteatsy_inbound_public_key"))
    external_fiteatsy_inbound_public_keys: str | None = Field(default=None, validation_alias=AliasChoices("EXTERNAL_FITEATSY_INBOUND_PUBLIC_KEYS", "external_fiteatsy_inbound_public_keys"))
    external_fiteatsy_inbound_issuer: str = Field(default="fiteatsy-auth-service", validation_alias=AliasChoices("EXTERNAL_FITEATSY_INBOUND_ISSUER", "external_fiteatsy_inbound_issuer"))
    external_fiteatsy_inbound_audience: str = Field(default="practice-operations-service", validation_alias=AliasChoices("EXTERNAL_FITEATSY_INBOUND_AUDIENCE", "external_fiteatsy_inbound_audience"))
    external_fiteatsy_backend_url: str | None = Field(default=None, validation_alias=AliasChoices("EXTERNAL_FITEATSY_BACKEND_URL", "external_fiteatsy_backend_url"))
    external_fiteatsy_outbound_private_key: str | None = Field(default=None, validation_alias=AliasChoices("EXTERNAL_FITEATSY_OUTBOUND_PRIVATE_KEY", "external_fiteatsy_outbound_private_key"))
    external_fiteatsy_outbound_key_id: str | None = Field(default=None, validation_alias=AliasChoices("EXTERNAL_FITEATSY_OUTBOUND_KEY_ID", "external_fiteatsy_outbound_key_id"))
    external_fiteatsy_outbound_issuer: str = Field(default="zestiva-platform", validation_alias=AliasChoices("EXTERNAL_FITEATSY_OUTBOUND_ISSUER", "external_fiteatsy_outbound_issuer"))
    external_fiteatsy_outbound_audience: str = Field(default="fiteatsy-backend", validation_alias=AliasChoices("EXTERNAL_FITEATSY_OUTBOUND_AUDIENCE", "external_fiteatsy_outbound_audience"))

    model_config = {"env_file": ".env", "case_sensitive": False}

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if isinstance(value, str) and value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix):]
        return value

    @field_validator("external_fiteatsy_inbound_public_keys", mode="before")
    @classmethod
    def validate_fiteatsy_inbound_keyring(cls, value: str | None) -> str | None:
        if value:
            parse_public_keyring(value)
        return value

    @model_validator(mode="after")
    def production_database_required(self):
        if self.app_env.lower() == "production" and ("localhost" in self.database_url or "127.0.0.1" in self.database_url):
            raise ValueError("DATABASE_URL must use production PostgreSQL")
        if self.app_env.lower() == "production" and self.profession_intake_secret == "development-profession-intake-secret":
            raise ValueError("PROFESSION_INTAKE_SECRET must be set in production")
        if self.app_env.lower() == "production" and self.client_portal_secret == "development-client-portal-secret":
            raise ValueError("CLIENT_PORTAL_SECRET must be set in production")
        if self.app_env.lower() == "production" and self.private_notes_encryption_key == "development-private-notes-key":
            raise ValueError("PRIVATE_NOTES_ENCRYPTION_KEY must be set in production")
        if self.app_env.lower() == "production" and not self.qa_delegation_public_key:
            raise ValueError("QA_DELEGATION_PUBLIC_KEY must be set in production")
        if self.external_fiteatsy_connection_enabled and not self.external_fiteatsy_pin_pepper:
            raise ValueError("EXTERNAL_FITEATSY_PIN_PEPPER must be set when Fiteatsy connections are enabled")
        if self.external_fiteatsy_connection_enabled and not (self.external_fiteatsy_inbound_public_keys or self.external_fiteatsy_inbound_public_key):
            raise ValueError("A Fiteatsy inbound assertion verifier must be set when Fiteatsy connections are enabled")
        if self.external_fiteatsy_health_access_enabled and not all((self.external_fiteatsy_backend_url, self.external_fiteatsy_outbound_private_key, self.external_fiteatsy_outbound_key_id)):
            raise ValueError("Fiteatsy outbound URL and signing credentials must be set when health access is enabled")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
