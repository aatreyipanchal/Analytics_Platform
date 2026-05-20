from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.dashboard import Dashboard, Widget, WidgetType
from app.models.event import Event
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardInDB,
    DashboardTemplate,
    DashboardUpdate,
    WidgetCreate,
    WidgetInDB,
    WidgetQueryResult,
)
from app.services.cache import get_cached_json, set_cached_json

router = APIRouter()

TEMPLATES: list[DashboardTemplate] = [
    DashboardTemplate(
        slug="web-analytics",
        name="Web Analytics",
        description="Traffic, conversion, and event mix for product teams.",
        widgets=[
            {"title": "Daily signups", "type": WidgetType.LINE, "configuration": {"event_name": "signup_completed", "bucket": "day"}},
            {"title": "Traffic sources", "type": WidgetType.PIE, "configuration": {}},
            {"title": "Events in last 7 days", "type": WidgetType.KPI, "configuration": {"label": "Events"}},
        ],
    ),
    DashboardTemplate(
        slug="sales-funnel",
        name="Sales Funnel",
        description="Lead and order volume views for commercial teams.",
        widgets=[
            {"title": "Lead volume", "type": WidgetType.BAR, "configuration": {"event_name": "lead_created", "bucket": "day"}},
            {"title": "Won deals", "type": WidgetType.LINE, "configuration": {"event_name": "deal_won", "bucket": "day"}},
            {"title": "Top funnel stages", "type": WidgetType.PIE, "configuration": {}},
        ],
    ),
]


async def _get_dashboard_for_user(db: AsyncSession, dashboard_id: int, user: User) -> Dashboard:
    dashboard = await db.scalar(
        select(Dashboard)
        .options(selectinload(Dashboard.widgets))
        .where(Dashboard.id == dashboard_id, Dashboard.organization_id == user.organization_id)
    )
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dashboard


def _resolve_range(hours: int) -> tuple[datetime, datetime]:
    end_at = datetime.now(timezone.utc)
    start_at = end_at - timedelta(hours=hours)
    return start_at, end_at


async def _build_widget_data(
    db: AsyncSession,
    widget: Widget,
    organization_id: int,
    hours: int,
) -> WidgetQueryResult:
    config = widget.configuration
    start_at, end_at = _resolve_range(hours)
    base_filters = [
        Event.organization_id == organization_id,
        Event.timestamp >= start_at,
        Event.timestamp <= end_at,
    ]
    event_name = config.get("event_name")
    if event_name:
        base_filters.append(Event.event_name == event_name)

    if widget.type in {WidgetType.LINE, WidgetType.BAR}:
        bucket = config.get("bucket", "day")
        bucket_expr = func.date_trunc(bucket, Event.timestamp)
        rows = (
            await db.execute(
                select(bucket_expr.label("bucket"), func.count(Event.id).label("value"))
                .where(*base_filters)
                .group_by(bucket_expr)
                .order_by(bucket_expr.asc())
            )
        ).all()
        data = [{"label": row.bucket.isoformat(), "value": row.value} for row in rows]
    elif widget.type == WidgetType.PIE:
        rows = (
            await db.execute(
                select(Event.event_name.label("label"), func.count(Event.id).label("value"))
                .where(*base_filters)
                .group_by(Event.event_name)
                .order_by(func.count(Event.id).desc())
            )
        ).all()
        data = [{"label": row.label, "value": row.value} for row in rows]
    elif widget.type == WidgetType.KPI:
        total = await db.scalar(select(func.count(Event.id)).where(*base_filters))
        data = [{"label": config.get("label", "Total events"), "value": total or 0}]
    else:
        rows = (
            await db.execute(
                select(
                    Event.event_name,
                    Event.user_id,
                    Event.timestamp,
                )
                .where(*base_filters)
                .order_by(Event.timestamp.desc())
                .limit(10)
            )
        ).all()
        data = [
            {
                "event_name": row.event_name,
                "user_id": row.user_id,
                "timestamp": row.timestamp.isoformat(),
            }
            for row in rows
        ]

    return WidgetQueryResult(widget_id=widget.id, widget_type=widget.type, title=widget.title, data=data)


@router.get("/", response_model=list[DashboardInDB])
async def list_dashboards(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[DashboardInDB]:
    dashboards = list(
        (
            await db.execute(
                select(Dashboard)
                .options(selectinload(Dashboard.widgets))
                .where(Dashboard.organization_id == current_user.organization_id)
                .order_by(Dashboard.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return dashboards


@router.get("/templates", response_model=list[DashboardTemplate])
async def list_dashboard_templates() -> list[DashboardTemplate]:
    return TEMPLATES


@router.post("/", response_model=DashboardInDB, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_in: DashboardCreate,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> DashboardInDB:
    dashboard = Dashboard(
        name=dashboard_in.name,
        description=dashboard_in.description,
        is_public=dashboard_in.is_public,
        refresh_interval_seconds=dashboard_in.refresh_interval_seconds,
        organization_id=current_user.organization_id,
    )
    db.add(dashboard)
    await db.commit()
    return await _get_dashboard_for_user(db, dashboard.id, current_user)


@router.post("/templates/{template_slug}", response_model=DashboardInDB, status_code=status.HTTP_201_CREATED)
async def create_dashboard_from_template(
    template_slug: str,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> DashboardInDB:
    template = next((item for item in TEMPLATES if item.slug == template_slug), None)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    dashboard = Dashboard(
        name=template.name,
        description=template.description,
        is_public=False,
        refresh_interval_seconds=60,
        organization_id=current_user.organization_id,
    )
    db.add(dashboard)
    await db.flush()

    for position, widget_template in enumerate(template.widgets):
        db.add(
            Widget(
                dashboard_id=dashboard.id,
                title=widget_template.title,
                type=widget_template.type,
                position=position,
                configuration=widget_template.configuration,
            )
        )

    await db.commit()
    return await _get_dashboard_for_user(db, dashboard.id, current_user)


@router.patch("/{dashboard_id}", response_model=DashboardInDB)
async def update_dashboard(
    dashboard_id: int,
    dashboard_in: DashboardUpdate,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> DashboardInDB:
    dashboard = await _get_dashboard_for_user(db, dashboard_id, current_user)
    updates = dashboard_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(dashboard, field, value)
    await db.commit()
    return await _get_dashboard_for_user(db, dashboard.id, current_user)


@router.post("/{dashboard_id}/widgets", response_model=WidgetInDB, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: int,
    widget_in: WidgetCreate,
    current_user: User = Depends(deps.verify_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(deps.get_db),
) -> WidgetInDB:
    dashboard = await _get_dashboard_for_user(db, dashboard_id, current_user)
    widget = Widget(
        dashboard_id=dashboard.id,
        type=widget_in.type,
        title=widget_in.title,
        position=widget_in.position,
        configuration=widget_in.configuration,
    )
    db.add(widget)
    await db.commit()
    await db.refresh(widget)
    return widget


@router.get("/{dashboard_id}/data", response_model=list[WidgetQueryResult])
async def get_dashboard_data(
    dashboard_id: int,
    hours: int = Query(default=168, ge=1, le=24 * 90),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[WidgetQueryResult]:
    cache_key = f"dashboard:{current_user.organization_id}:{dashboard_id}:{hours}"
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return [WidgetQueryResult.model_validate(item) for item in cached]

    dashboard = await _get_dashboard_for_user(db, dashboard_id, current_user)
    results: list[WidgetQueryResult] = []
    for widget in sorted(dashboard.widgets, key=lambda item: item.position):
        results.append(await _build_widget_data(db, widget, current_user.organization_id, hours))
    await set_cached_json(cache_key, [item.model_dump(mode="json") for item in results])
    return results


@router.get("/public/{dashboard_id}", response_model=DashboardInDB)
async def get_public_dashboard(dashboard_id: int, db: AsyncSession = Depends(deps.get_db)) -> DashboardInDB:
    dashboard = await db.scalar(
        select(Dashboard).options(selectinload(Dashboard.widgets)).where(Dashboard.id == dashboard_id, Dashboard.is_public.is_(True))
    )
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dashboard


@router.get("/public/{dashboard_id}/data", response_model=list[WidgetQueryResult])
async def get_public_dashboard_data(
    dashboard_id: int,
    hours: int = Query(default=168, ge=1, le=24 * 90),
    db: AsyncSession = Depends(deps.get_db),
) -> list[WidgetQueryResult]:
    dashboard = await db.scalar(
        select(Dashboard).options(selectinload(Dashboard.widgets)).where(Dashboard.id == dashboard_id, Dashboard.is_public.is_(True))
    )
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    results: list[WidgetQueryResult] = []
    for widget in sorted(dashboard.widgets, key=lambda item: item.position):
        results.append(await _build_widget_data(db, widget, dashboard.organization_id, hours))
    return results
