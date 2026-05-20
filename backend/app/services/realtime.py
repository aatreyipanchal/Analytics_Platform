import json
from typing import Any

from app.core.redis_client import get_redis

EVENTS_CHANNEL_PREFIX = "realtime:org:"


def events_channel(organization_id: int) -> str:
    return f"{EVENTS_CHANNEL_PREFIX}{organization_id}:events"


def alerts_channel(organization_id: int) -> str:
    return f"{EVENTS_CHANNEL_PREFIX}{organization_id}:alerts"


async def publish_org_event(organization_id: int, payload: dict[str, Any]) -> None:
    redis = get_redis()
    message = json.dumps(payload, default=str)
    try:
        await redis.publish(events_channel(organization_id), message)
    except Exception:
        return


async def publish_org_alert(organization_id: int, payload: dict[str, Any]) -> None:
    redis = get_redis()
    message = json.dumps(payload, default=str)
    try:
        await redis.publish(alerts_channel(organization_id), message)
    except Exception:
        return
