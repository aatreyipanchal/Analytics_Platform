import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.core.redis_client import get_redis
from app.schemas.token import TokenPayload
from app.services.realtime import alerts_channel, events_channel

router = APIRouter()


async def _resolve_org_id(token: str) -> int:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    token_data = TokenPayload(**payload)
    if token_data.type != "access" or token_data.org is None:
        raise ValueError("Invalid token")
    return int(token_data.org)


@router.websocket("/events")
async def events_stream(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        organization_id = await _resolve_org_id(token)
    except (JWTError, ValueError):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    redis = get_redis()
    pubsub = redis.pubsub()
    channel = events_channel(organization_id)
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.websocket("/alerts")
async def alerts_stream(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        organization_id = await _resolve_org_id(token)
    except (JWTError, ValueError):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    redis = get_redis()
    pubsub = redis.pubsub()
    channel = alerts_channel(organization_id)
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
