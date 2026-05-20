from alembic import command

from app.core.alembic_config import get_alembic_config
from app.core.logging import get_logger

logger = get_logger(__name__)


def run_migrations() -> None:
    alembic_cfg = get_alembic_config()
    logger.info("running_migrations")
    command.upgrade(alembic_cfg, "head")
