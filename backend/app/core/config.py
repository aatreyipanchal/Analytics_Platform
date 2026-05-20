from functools import cached_property
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    PROJECT_NAME: str = "Pulseboard Analytics"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    SECRET_KEY: str = Field(
        default="change-me-in-production-change-me-in-production",
        min_length=32,
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INVITATION_TOKEN_EXPIRE_HOURS: int = 72

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "analytics_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = True
    AUTO_CREATE_TABLES: bool = True
    RUN_MIGRATIONS_ON_STARTUP: bool = False

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    FRONTEND_URL: str = "http://localhost:3000"
    REFRESH_COOKIE_NAME: str = "analytics_refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: Literal["lax", "none", "strict"] = "lax"

    DEFAULT_DASHBOARD_REFRESH_SECONDS: int = 60
    RATE_LIMIT_PER_MINUTE: int = 240
    DASHBOARD_CACHE_TTL_SECONDS: int = 30
    LOG_LEVEL: str = "INFO"

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            import json

            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def apply_production_defaults(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            object.__setattr__(self, "REFRESH_COOKIE_SECURE", True)
            object.__setattr__(self, "REFRESH_COOKIE_SAMESITE", "none")
            object.__setattr__(self, "AUTO_CREATE_TABLES", False)
            object.__setattr__(self, "CELERY_TASK_ALWAYS_EAGER", False)
            object.__setattr__(self, "RUN_MIGRATIONS_ON_STARTUP", True)
        return self

    @cached_property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @cached_property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return str(
            URL.create(
                "postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                database=self.POSTGRES_DB,
            )
        )

    @cached_property
    def sqlalchemy_sync_database_uri(self) -> str:
        uri = self.sqlalchemy_database_uri
        return uri.replace("postgresql+asyncpg://", "postgresql://")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
