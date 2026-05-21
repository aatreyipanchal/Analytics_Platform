# Assessment Requirements Coverage

**Live deployment (verified May 2026)**

| Service | URL |
|---------|-----|
| Frontend | https://analytics-platform-bay.vercel.app/ |
| Backend API | https://analytics-platform-2-kpih.onrender.com |
| API docs (Swagger) | https://analytics-platform-2-kpih.onrender.com/docs |
| Health | https://analytics-platform-2-kpih.onrender.com/health |
| Metrics | https://analytics-platform-2-kpih.onrender.com/metrics |

**REST base:** `https://analytics-platform-2-kpih.onrender.com/api/v1`  
**WebSocket base:** `wss://analytics-platform-2-kpih.onrender.com/api/v1`

Run automated smoke test: `python backend/scripts/smoke_test_live.py` (targets the URLs above).

---

## Must Have

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Email/password auth (bcrypt) | Done | https://analytics-platform-2-kpih.onrender.com/api/v1/auth/signup · `backend/app/api/v1/auth.py` |
| JWT access + refresh cookie | Done | https://analytics-platform-2-kpih.onrender.com/api/v1/auth/login · `/auth/refresh` |
| Organization on signup | Done | Signup creates org + Owner on live API |
| Invite-based onboarding | Done | https://analytics-platform-2-kpih.onrender.com/api/v1/auth/invitations · Team page on Vercel |
| Roles Owner/Admin/Analyst/Viewer | Done | `UserRole`, `verify_role` in `backend/app/api/deps.py` |
| Org data isolation | Done | Queries filter by `organization_id` |
| Event API single + batch | Done | `POST https://analytics-platform-2-kpih.onrender.com/api/v1/events` · `/events/batch` |
| CSV upload | Done | `POST https://analytics-platform-2-kpih.onrender.com/api/v1/events/upload/csv` |
| Webhook-style ingestion | Done | `POST https://analytics-platform-2-kpih.onrender.com/api/v1/events/webhook` |
| Pydantic validation | Done | `backend/app/schemas/event.py` |
| Celery async processing | Done | `backend/app/workers/tasks.py` (Render worker) |
| API key create/rotate/revoke | Done | https://analytics-platform-2-kpih.onrender.com/api/v1/organizations/api-keys |
| Rate limiting | Done | Redis `backend/app/services/rate_limit.py` |
| Custom dashboards | Done | https://analytics-platform-bay.vercel.app/workspace/dashboards |
| Widgets line/bar/pie/KPI/table | Done | `GET .../api/v1/dashboards/{id}/data?hours=` · `WidgetPanel` |
| Configurable time range | Done | `?hours=` on dashboard data endpoint |
| Dashboard sharing (public) | Done | `is_public`, public dashboard routes |
| Dashboard templates | Done | `GET https://analytics-platform-2-kpih.onrender.com/api/v1/dashboards/templates` |

## Should Have

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Threshold alerts | Done | https://analytics-platform-bay.vercel.app/workspace/alerts · `backend/app/api/v1/alerts.py` |
| Celery Beat scheduling | Done | `backend/app/workers/celery_app.py` (Render Beat worker) |
| In-app notifications | Done | `GET https://analytics-platform-2-kpih.onrender.com/api/v1/alerts/notifications` |
| Email alerts | Partial | SMTP optional in `backend/.env` / Render env |
| Webhook alerts | Done | `backend/app/services/alerts.py` |
| WebSocket dashboard/events | Done | `wss://analytics-platform-2-kpih.onrender.com/api/v1/realtime/events` |
| Live event stream | Done | Ingestion page WebSocket on Vercel |

## Architecture & Production

| Requirement | Status | Evidence |
|-------------|--------|----------|
| FastAPI + SQLAlchemy 2 async | Done | Throughout `backend/app/` |
| Alembic migrations | Done | `backend/alembic/versions/001_initial_schema.py` · `scripts/start.sh` on Render |
| Clean layering | Done | api → services → repositories → models |
| structlog + correlation IDs | Done | `backend/app/core/logging.py`, middleware |
| Health + metrics | Done | https://analytics-platform-2-kpih.onrender.com/health · `/metrics` |
| Render + Vercel deploy | Done | API on Render · app on Vercel (URLs above) |
| Docker Compose | Done | `docker-compose.yml` |
| GitHub Actions CI | Done | `.github/workflows/ci.yml` |

## UI/UX Rubric

| Requirement | Status | Notes |
|-------------|--------|-------|
| Responsive layout | Done | Tailwind, mobile-friendly shell |
| Chart interactions | Partial | Recharts tooltips; no drill-down |
| Loading states | Done | Per-page loading + spinner component |
| Optimistic updates | Partial | Disabled buttons during submit |
| Accessibility basics | Partial | Landmarks, aria labels on nav/forms |

## Not Implemented (documented gaps)

| Item | Reason |
|------|--------|
| Drag-and-drop widget layout | Position index only |
| Saved query entities | Widget config uses `event_name` |
| Full-screen presentation mode | Out of scope for timeline |
| Scheduled PDF reports | Out of scope |
| Google OAuth | Optional per brief |
| GraphQL, OpenTelemetry, Locust, feature flags | Bonus only |

## Recommended reviewer flow (3 min)

1. Open https://analytics-platform-bay.vercel.app/ → sign up or sign in  
2. **Ingestion** — https://analytics-platform-bay.vercel.app/workspace/ingestion → create API key → submit sample event  
3. **Dashboards** — https://analytics-platform-bay.vercel.app/workspace/dashboards → use template → confirm charts after refresh  
4. **Alerts** — https://analytics-platform-bay.vercel.app/workspace/alerts → create rule on `error_logged` (optional)  
5. **Team** — https://analytics-platform-bay.vercel.app/workspace/team → invite link  
6. Optional: open https://analytics-platform-2-kpih.onrender.com/docs and https://analytics-platform-2-kpih.onrender.com/health
