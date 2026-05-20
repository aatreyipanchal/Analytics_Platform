from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.exceptions import NotFoundError
from app.models.alert import Alert, AlertHistory, AlertStatus, Notification
from app.models.user import User, UserRole
from app.schemas.alert import AlertCreate, AlertHistoryInDB, AlertInDB, AlertMute, AlertUpdate, NotificationInDB

router = APIRouter()


async def _get_alert(db: AsyncSession, alert_id: int, user: User) -> Alert:
    alert = await db.scalar(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
            Alert.deleted_at.is_(None),
        )
    )
    if not alert:
        raise NotFoundError("Alert not found")
    return alert


@router.get("/", response_model=list[AlertInDB])
async def list_alerts(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[AlertInDB]:
    rows = list(
        (
            await db.execute(
                select(Alert)
                .where(Alert.organization_id == current_user.organization_id, Alert.deleted_at.is_(None))
                .order_by(Alert.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return rows


@router.post("/", response_model=AlertInDB, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_in: AlertCreate,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> AlertInDB:
    alert = Alert(
        organization_id=current_user.organization_id,
        name=alert_in.name,
        event_name=alert_in.event_name,
        threshold=alert_in.threshold,
        window_minutes=alert_in.window_minutes,
        webhook_url=alert_in.webhook_url,
        notify_email=alert_in.notify_email,
        status=AlertStatus.ACTIVE,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=AlertInDB)
async def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> AlertInDB:
    alert = await _get_alert(db, alert_id, current_user)
    for field, value in alert_in.model_dump(exclude_unset=True).items():
        setattr(alert, field, value)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.post("/{alert_id}/mute", response_model=AlertInDB)
async def mute_alert(
    alert_id: int,
    mute_in: AlertMute,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> AlertInDB:
    alert = await _get_alert(db, alert_id, current_user)
    alert.status = AlertStatus.MUTED
    alert.muted_until = datetime.now(timezone.utc) + timedelta(minutes=mute_in.minutes)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(deps.verify_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(deps.get_db),
) -> None:
    alert = await _get_alert(db, alert_id, current_user)
    alert.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.get("/{alert_id}/history", response_model=list[AlertHistoryInDB])
async def alert_history(
    alert_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[AlertHistoryInDB]:
    await _get_alert(db, alert_id, current_user)
    rows = list(
        (
            await db.execute(
                select(AlertHistory)
                .where(AlertHistory.alert_id == alert_id)
                .order_by(AlertHistory.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    return rows


@router.get("/notifications/list", response_model=list[NotificationInDB])
async def list_notifications(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[NotificationInDB]:
    rows = list(
        (
            await db.execute(
                select(Notification)
                .where(Notification.organization_id == current_user.organization_id)
                .order_by(Notification.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    return rows


@router.post("/notifications/{notification_id}/read", response_model=NotificationInDB)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> NotificationInDB:
    notification = await db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.organization_id == current_user.organization_id,
        )
    )
    if not notification:
        raise NotFoundError("Notification not found")
    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return notification
