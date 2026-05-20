import asyncio
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.alert import Alert, AlertHistory, AlertStatus, Notification
from app.models.event import Event
from app.services.realtime import publish_org_alert

logger = get_logger(__name__)


async def evaluate_alerts_for_org(db: AsyncSession, organization_id: int) -> None:
    now = datetime.now(timezone.utc)
    alerts = list(
        (
            await db.execute(
                select(Alert).where(
                    Alert.organization_id == organization_id,
                    Alert.deleted_at.is_(None),
                    Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.TRIGGERED]),
                )
            )
        )
        .scalars()
        .all()
    )

    for alert in alerts:
        if alert.status == AlertStatus.MUTED and alert.muted_until and alert.muted_until > now:
            continue
        if alert.muted_until and alert.muted_until <= now:
            alert.status = AlertStatus.ACTIVE
            alert.muted_until = None

        window_start = now - timedelta(minutes=alert.window_minutes)
        count = await db.scalar(
            select(func.count(Event.id)).where(
                Event.organization_id == organization_id,
                Event.event_name == alert.event_name,
                Event.timestamp >= window_start,
            )
        )
        current_value = float(count or 0)
        triggered = current_value > alert.threshold

        if triggered and alert.status != AlertStatus.TRIGGERED:
            alert.status = AlertStatus.TRIGGERED
            message = (
                f"{alert.name}: {alert.event_name} count {int(current_value)} "
                f"exceeded threshold {alert.threshold} in {alert.window_minutes}m"
            )
            history = AlertHistory(alert_id=alert.id, triggered_value=current_value, message=message)
            db.add(history)
            notification = Notification(
                organization_id=organization_id,
                title=f"Alert triggered: {alert.name}",
                message=message,
                alert_id=alert.id,
            )
            db.add(notification)
            await db.flush()
            await _dispatch_alert_notifications(alert, message, current_value)
            await publish_org_alert(
                organization_id,
                {
                    "type": "alert_triggered",
                    "alert_id": alert.id,
                    "name": alert.name,
                    "value": current_value,
                    "message": message,
                },
            )
        elif not triggered and alert.status == AlertStatus.TRIGGERED:
            alert.status = AlertStatus.RESOLVED
            await publish_org_alert(
                organization_id,
                {"type": "alert_resolved", "alert_id": alert.id, "name": alert.name},
            )


async def _dispatch_alert_notifications(alert: Alert, message: str, value: float) -> None:
    if alert.webhook_url:
        payload = {
            "text": message,
            "alert": alert.name,
            "event_name": alert.event_name,
            "value": value,
            "threshold": alert.threshold,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(alert.webhook_url, json=payload)
        except Exception as exc:
            logger.warning("webhook_delivery_failed", alert_id=alert.id, error=str(exc))

    if alert.notify_email and settings.SMTP_HOST and settings.SMTP_FROM_EMAIL:
        await asyncio.to_thread(_send_email, alert.notify_email, f"[Pulseboard] {alert.name}", message)


def _send_email(to_email: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def evaluate_all_alerts() -> None:
    async with AsyncSessionLocal() as db:
        org_ids = list((await db.execute(select(Alert.organization_id).distinct())).scalars().all())
        for org_id in org_ids:
            await evaluate_alerts_for_org(db, org_id)
        await db.commit()
