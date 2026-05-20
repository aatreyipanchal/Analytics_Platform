import asyncio
from datetime import datetime
from typing import Any

from app.core.db import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.event import Event
from app.services.alerts import evaluate_all_alerts
from app.services.realtime import publish_org_event
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


async def process_batch_events_async(
    events_data: list[dict[str, Any]],
    organization_id: int,
    source: str = "api",
) -> None:
    async with AsyncSessionLocal() as session:
        for event_data in events_data:
            timestamp = event_data["timestamp"]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            session.add(
                Event(
                    event_name=event_data["event_name"],
                    timestamp=timestamp,
                    user_id=event_data["user_id"],
                    properties=event_data.get("properties", {}),
                    source=source,
                    organization_id=organization_id,
                )
            )
        await session.commit()

    for event_data in events_data:
        await publish_org_event(
            organization_id,
            {
                "type": "event_ingested",
                "event_name": event_data["event_name"],
                "user_id": event_data.get("user_id"),
                "timestamp": event_data.get("timestamp"),
            },
        )


@celery_app.task(name="app.workers.tasks.process_batch_events", bind=True, max_retries=3)
def process_batch_events(
    self,
    events_data: list[dict[str, Any]],
    organization_id: int,
    source: str = "api",
) -> None:
    try:
        asyncio.run(process_batch_events_async(events_data, organization_id, source))
    except Exception as exc:
        logger.exception("process_batch_events_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) from exc


@celery_app.task(name="app.workers.tasks.evaluate_alerts_task")
def evaluate_alerts_task() -> None:
    asyncio.run(evaluate_all_alerts())
