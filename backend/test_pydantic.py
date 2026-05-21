from pydantic_settings import BaseSettings, SettingsConfigDict
import os

os.environ["ENVIRONMENT"] = "production"
os.environ["DATABASE_URL"] = "postgres://user:pass@dpg-cabc123-a/dbname"

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("ENVIRONMENT", "development") != "production" else None,
        case_sensitive=True,
        extra="ignore",
    )

s = Settings()
print("ENV:", s.ENVIRONMENT)
print("DB URL:", s.DATABASE_URL)
