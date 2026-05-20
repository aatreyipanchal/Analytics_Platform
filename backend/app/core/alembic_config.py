"""Alembic Config helper for programmatic migrations (run_migrations)."""

from alembic.config import Config

from app.core.config import settings


def escaped_sync_database_uri() -> str:
    """Escape % for ConfigParser when setting sqlalchemy.url on a Config object."""
    return settings.sqlalchemy_sync_database_uri.replace("%", "%%")


def get_alembic_config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", escaped_sync_database_uri())
    return cfg
