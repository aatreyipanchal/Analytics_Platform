import asyncio
from datetime import datetime
from typing import Any

from app.core.db import AsyncSessionLocal
from app.models.event import Event
from app.workers.celery_app import celery_app


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


@celery_app.task(name="app.workers.tasks.process_batch_events")
def process_batch_events(events_data: list[dict[str, Any]], organization_id: int, source: str = "api") -> None:
    asyncio.run(process_batch_events_async(events_data, organization_id, source))
