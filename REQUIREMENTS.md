# Assessment Requirements Coverage

Live demo (verified May 2026):

| Service | URL |
|---------|-----|
| Frontend | https://analytics-platform-bay.vercel.app/ |
| Backend API | https://analytics-platform-2-kpih.onrender.com |
| API docs | https://analytics-platform-2-kpih.onrender.com/docs |
| Health | https://analytics-platform-2-kpih.onrender.com/health |

Run automated smoke test: `python backend/scripts/smoke_test_live.py`

---

## Must Have

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Email/password auth (bcrypt) | Done | `backend/app/api/v1/auth.py`, `core/security.py` |
| JWT access + refresh cookie | Done | Login/signup/refresh endpoints |
| Organization on signup | Done | Signup creates org + Owner |
| Invite-based onboarding | Done | `/auth/invitations`, team page |
| Roles Owner/Admin/Analyst/Viewer | Done | `UserRole`, `verify_role` deps |
| Org data isolation | Done | Queries filter by `organization_id` |
| Event API single + batch | Done | `POST /events`, `POST /events/batch` |
| CSV upload | Done | `POST /events/upload/csv` |
| Webhook-style ingestion | Done | `POST /events/webhook` |
| Pydantic validation | Done | `schemas/event.py` |
| Celery async processing | Done | `workers/tasks.py` |
| API key create/rotate/revoke | Done | `organizations/api-keys` |
| Rate limiting | Done | Redis `services/rate_limit.py` |
| Custom dashboards | Done | Dashboards workspace |
| Widgets line/bar/pie/KPI/table | Done | `WidgetPanel`, dashboard data API |
| Configurable time range | Done | `?hours=` query param |
| Dashboard sharing (public) | Done | `is_public`, public endpoints |
| Dashboard templates | Done | Web Analytics, Sales Funnel |

## Should Have

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Threshold alerts | Done | `models/alert.py`, alerts page |
| Celery Beat scheduling | Done | `celery_app.py` beat schedule |
| In-app notifications | Done | `notifications` table + API |
| Email alerts | Partial | SMTP optional in config |
| Webhook alerts | Done | `services/alerts.py` |
| WebSocket dashboard/events | Done | `api/v1/realtime.py` |
| Live event stream | Done | Ingestion page WebSocket |

## Architecture & Production

| Requirement | Status | Evidence |
|-------------|--------|----------|
| FastAPI + SQLAlchemy 2 async | Done | Throughout backend |
| Alembic migrations | Done | `alembic/versions/001_initial_schema.py` |
| Clean layering | Done | api → services → repositories → models |
| structlog + correlation IDs | Done | `core/logging.py`, middleware |
| Health + metrics | Done | `/health`, `/metrics` |
| Render + Vercel deploy | Done | Live URLs above |
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

1. Open frontend → sign up or sign in  
2. **Ingestion** → create API key → submit sample event  
3. **Dashboards** → use template → confirm charts after refresh  
4. **Alerts** → create rule on `error_logged` → optional  
5. **Team** → invite link  
