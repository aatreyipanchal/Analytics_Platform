from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.db import engine
from app.core.handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import CorrelationIdMiddleware
from app.core.migrations import run_migrations
from app.models.api_key import ApiKey  # noqa: F401
from app.models.alert import Alert, AlertHistory, Notification  # noqa: F401
from app.models.base import Base
from app.models.dashboard import Dashboard, Widget  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.invitation import Invitation  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "startup_config",
        environment=settings.ENVIRONMENT,
        has_database_url=bool(settings.DATABASE_URL),
        auto_create_tables=settings.AUTO_CREATE_TABLES,
        run_migrations=settings.RUN_MIGRATIONS_ON_STARTUP,
    )

    # Production: schema is created by `scripts/start.sh` (alembic). Do not connect here.
    if settings.RUN_MIGRATIONS_ON_STARTUP:
        run_migrations()
    elif settings.AUTO_CREATE_TABLES and settings.ENVIRONMENT == "development":
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    logger.info("app_started", environment=settings.ENVIRONMENT, version=settings.VERSION)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/metrics")
def metrics():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
