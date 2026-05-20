from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.core.redis_client import get_redis


async def enforce_ingestion_rate_limit(organization_id: int, incoming_count: int) -> None:
    minute_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"ratelimit:org:{organization_id}:{minute_bucket}"
    redis = get_redis()
    try:
        current = await redis.incrby(key, incoming_count)
        if current == incoming_count:
            await redis.expire(key, 120)
        if current > settings.RATE_LIMIT_PER_MINUTE:
            raise RateLimitError(
                f"Ingestion rate limit exceeded ({settings.RATE_LIMIT_PER_MINUTE}/minute)",
            )
    except RateLimitError:
        raise
    except Exception:
        # Redis unavailable: allow request (degraded mode for local dev without Redis)
        return
