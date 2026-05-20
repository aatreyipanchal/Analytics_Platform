import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Security, UploadFile, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.exceptions import UnauthorizedError
from app.core.security import hash_api_key
from app.models.api_key import ApiKey
from app.models.event import Event
from app.models.organization import Organization
from app.models.user import User
from app.schemas.event import EventBatchCreate, EventCreate, EventInDB, EventIngestionResponse
from app.services.rate_limit import enforce_ingestion_rate_limit
from app.workers.tasks import process_batch_events, process_batch_events_async
from app.core.config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key")


async def get_organization_by_api_key(
    db: AsyncSession = Depends(deps.get_db),
    api_key: str = Security(api_key_header),
) -> Organization:
    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(ApiKey, Organization)
        .join(Organization, ApiKey.organization_id == Organization.id)
        .where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
    )
    pair = result.first()
    if not pair:
        raise UnauthorizedError("Invalid API key")

    key_record, organization = pair
    from datetime import datetime, timezone

    key_record.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return organization


async def _queue_events(events: list[dict[str, Any]], organization_id: int, source: str) -> EventIngestionResponse:
    await enforce_ingestion_rate_limit(organization_id, len(events))
    if settings.CELERY_TASK_ALWAYS_EAGER:
        await process_batch_events_async(events, organization_id, source)
        return EventIngestionResponse(status="accepted", accepted=len(events))
    process_batch_events.delay(events, organization_id, source)
    return EventIngestionResponse(status="accepted", accepted=len(events))


@router.get("/recent", response_model=list[EventInDB])
async def list_recent_events(
    limit: int = 20,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[EventInDB]:
    rows = list(
        (
            await db.execute(
                select(Event)
                .where(Event.organization_id == current_user.organization_id)
                .order_by(Event.timestamp.desc())
                .limit(min(max(limit, 1), 100))
            )
        )
        .scalars()
        .all()
    )
    return rows


@router.post("/", response_model=EventIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(
    event_in: EventCreate,
    organization: Organization = Depends(get_organization_by_api_key),
) -> EventIngestionResponse:
    return await _queue_events([event_in.model_dump(mode="json")], organization.id, "api")


@router.post("/batch", response_model=EventIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_events(
    batch_in: EventBatchCreate,
    organization: Organization = Depends(get_organization_by_api_key),
) -> EventIngestionResponse:
    payload = [event.model_dump(mode="json") for event in batch_in.events]
    return await _queue_events(payload, organization.id, "api")


@router.post("/webhook", response_model=EventIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_webhook_payload(
    payload: dict[str, Any] = Body(...),
    organization: Organization = Depends(get_organization_by_api_key),
) -> EventIngestionResponse:
    if "events" in payload and isinstance(payload["events"], list):
        batch = EventBatchCreate.model_validate({"events": payload["events"]})
        events = [event.model_dump(mode="json") for event in batch.events]
        return await _queue_events(events, organization.id, "webhook")

    event = EventCreate.model_validate(payload)
    return await _queue_events([event.model_dump(mode="json")], organization.id, "webhook")


@router.post("/upload/csv", response_model=EventIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    file: UploadFile = File(...),
    organization: Organization = Depends(get_organization_by_api_key),
) -> EventIngestionResponse:
    from datetime import datetime

    from app.core.exceptions import AppError

    if not file.filename or not file.filename.endswith(".csv"):
        raise AppError("Only CSV files are supported", details={"filename": file.filename})

    contents = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))
    events: list[dict[str, Any]] = []
    for row in reader:
        try:
            event = EventCreate(
                event_name=row["event_name"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                user_id=row["user_id"],
                properties=json.loads(row.get("properties", "{}")),
            )
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        events.append(event.model_dump(mode="json"))

    if not events:
        raise AppError("No valid rows found in CSV")

    return await _queue_events(events, organization.id, "csv")
