"""Build SQLAlchemy URLs with correct encoding and Render Postgres SSL."""

from sqlalchemy.engine import URL, make_url


def _needs_ssl(database_url: str | None, environment: str) -> bool:
    if environment != "production" or not database_url:
        return False
    url = database_url.lower()
    return "render.com" in url or "dpg-" in url


def build_async_database_url(
    *,
    database_url: str | None,
    environment: str,
    postgres_user: str,
    postgres_password: str,
    postgres_server: str,
    postgres_port: int,
    postgres_db: str,
) -> URL:
    if database_url:
        url = database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = make_url(url)
    else:
        parsed = URL.create(
            "postgresql+asyncpg",
            username=postgres_user,
            password=postgres_password,
            host=postgres_server,
            port=postgres_port,
            database=postgres_db,
        )

    if _needs_ssl(database_url, environment):
        query = dict(parsed.query)
        if "sslmode" not in query:
            query["sslmode"] = "require"
        parsed = parsed.update_query_dict(query)
    return parsed


def build_sync_database_url(**kwargs) -> URL:
    return build_async_database_url(**kwargs).set(drivername="postgresql")
