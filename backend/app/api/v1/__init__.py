from fastapi import APIRouter

from app.api.v1 import alerts, auth, dashboards, events, organizations, realtime

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["realtime"])
