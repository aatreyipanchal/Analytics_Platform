import json
from typing import Any

from app.core.config import settings
from app.core.redis_client import get_redis


async def get_cached_json(key: str) -> Any | None:
    redis = get_redis()
    try:
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


async def set_cached_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    redis = get_redis()
    ttl = ttl_seconds or settings.DASHBOARD_CACHE_TTL_SECONDS
    try:
        await redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        return
