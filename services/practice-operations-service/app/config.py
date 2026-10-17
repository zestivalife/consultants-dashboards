from functools import lru_cache
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "practice-operations-service"
    app_env: str = "development"
    app_version: str = "0.1.0"
    app_commit_sha: str = Field(default="unknown", validation_alias=AliasChoices("APP_COMMIT_SHA", "RAILWAY_GIT_COMMIT_SHA"))
    app_port: int = Field(default=8006, validation_alias=AliasChoices("PORT", "APP_PORT"))
    database_url: str = "postgresql+asyncpg://nuetra:nuetra_secret@localhost:5432/nuetra_practice_operations"
    trusted_hosts: str = "*.railway.app,*.railway.internal,practice-operations-service,api-gateway,localhost,127.0.0.1"
    profession_intake_secret: str = Field(default="development-profession-intake-secret", validation_alias=AliasChoices("PROFESSION_INTAKE_SECRET", "profession_intake_secret"))
    profession_intake_public_url: str = Field(default="http://localhost:3000/profession-intake", validation_alias=AliasChoices("PROFESSION_INTAKE_PUBLIC_URL", "profession_intake_public_url"))

    model_config = {"env_file": ".env", "case_sensitive": False}

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if isinstance(value, str) and value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix):]
        return value

    @model_validator(mode="after")
    def production_database_required(self):
        if self.app_env.lower() == "production" and ("localhost" in self.database_url or "127.0.0.1" in self.database_url):
            raise ValueError("DATABASE_URL must use production PostgreSQL")
        if self.app_env.lower() == "production" and self.profession_intake_secret == "development-profession-intake-secret":
            raise ValueError("PROFESSION_INTAKE_SECRET must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
