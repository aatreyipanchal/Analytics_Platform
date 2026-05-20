from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.sqlalchemy_sync_database_uri)
    logger.info("running_migrations")
    command.upgrade(alembic_cfg, "head")
