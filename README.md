# Pulseboard Analytics

Production-ready multi-tenant analytics platform: FastAPI + PostgreSQL + Celery + Redis backend, Next.js 14 frontend.

## Features

| Module | Capabilities |
|--------|----------------|
| **Auth & tenancy** | JWT + refresh cookie, roles (Owner/Admin/Analyst/Viewer), invites, org isolation |
| **Ingestion** | Single/batch/webhook/CSV, API keys, Redis rate limits, async Celery processing |
| **Dashboards** | Templates, line/bar/pie/KPI/table widgets, public sharing, Redis query cache, auto-refresh |
| **Alerts** | Threshold rules, Celery Beat evaluation, in-app + webhook + optional email |
| **Real-time** | WebSocket event stream + alert push (Redis pub/sub) |
| **Ops** | Alembic migrations, structlog JSON logs, correlation IDs, `/health`, `/metrics` |

## Quick start (local)

### Prerequisites

- Python 3.11+, Node 20+, PostgreSQL, Redis

### Backend

```powershell
cd backend
copy .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

With Celery (set `CELERY_TASK_ALWAYS_EAGER=false` in `.env`):

```powershell
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

### Docker

```bash
docker compose up --build
```

## Deploy to production

**See [DEPLOYMENT.md](./DEPLOYMENT.md)** for step-by-step Render (backend + workers + DB + Redis) and Vercel (frontend) setup.

Summary:

1. Deploy `render.yaml` blueprint on Render
2. Set `FRONTEND_URL` and `BACKEND_CORS_ORIGINS` on the API service
3. Deploy `frontend/` on Vercel with `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_WS_BASE_URL`

## Project layout

```text
backend/
  alembic/          # DB migrations
  app/
    api/v1/         # REST + WebSocket routes
    core/           # config, logging, redis, migrations
    models/
    schemas/
    services/       # rate limit, cache, alerts, realtime
    workers/        # Celery tasks + Beat
  scripts/start.sh  # Render start command
frontend/
  app/workspace/    # ingestion, dashboards, alerts, team
render.yaml         # Render blueprint
DEPLOYMENT.md       # Full deployment guide
```

## API highlights

- `POST /api/v1/auth/signup` · `POST /api/v1/auth/login` · `POST /api/v1/auth/refresh`
- `POST /api/v1/events` (header `X-API-Key`)
- `GET /api/v1/dashboards/{id}/data?hours=168`
- `GET/POST /api/v1/alerts`
- `WS /api/v1/realtime/events?token=...`
- `GET /health` · `GET /metrics`

## Tests

```powershell
cd backend
pytest tests -q
```

## Environment

| File | Purpose |
|------|---------|
| `backend/.env.example` | Local + production backend vars |
| `frontend/.env.example` | API and WebSocket URLs for Vercel |
