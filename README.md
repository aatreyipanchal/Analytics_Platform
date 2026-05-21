# Pulseboard Analytics

Multi-tenant real-time analytics platform (AI Engineer assessment).

## Live demo

| | URL |
|---|-----|
| **App (Vercel)** | https://analytics-platform-bay.vercel.app/ |
| **API (Render)** | https://analytics-platform-2-kpih.onrender.com |
| **API docs** | https://analytics-platform-2-kpih.onrender.com/docs |
| **Health check** | https://analytics-platform-2-kpih.onrender.com/health |

**Quick test for reviewers:** Sign up → Ingestion (API key + sample event) → Dashboards (template) → optional Alerts.

- Full requirements matrix: [REQUIREMENTS.md](./REQUIREMENTS.md)
- Hiring team summary: [SUBMISSION.md](./SUBMISSION.md)
- Deploy guide: [DEPLOYMENT.md](./DEPLOYMENT.md)

```bash
# Verify production API (10 checks)
pip install httpx
python backend/scripts/smoke_test_live.py
```

> **Note:** Render free tier sleeps after inactivity; first load may take ~30 seconds.

---

## Features

| Module | Capabilities |
|--------|----------------|
| **Auth & tenancy** | JWT + refresh cookie, roles (Owner/Admin/Analyst/Viewer), invites, org isolation |
| **Ingestion** | Single/batch/webhook/CSV, API keys, Redis rate limits, async Celery processing |
| **Dashboards** | Templates, line/bar/pie/KPI/table widgets, public sharing, query cache, auto-refresh |
| **Alerts** | Threshold rules, Celery Beat, in-app + webhook + optional email |
| **Real-time** | WebSocket event stream + alert notifications |
| **Ops** | Alembic, structlog, correlation IDs, `/health`, `/metrics`, GitHub Actions CI |

---

## Quick start (local)

### Prerequisites

Python 3.11+, Node 20+, PostgreSQL, Redis

### Backend

```powershell
cd backend
copy .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Celery (when `CELERY_TASK_ALWAYS_EAGER=false`):

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

---

## Deploy to production

See [DEPLOYMENT.md](./DEPLOYMENT.md). Production URLs above use:

- Render: API + Postgres + Redis + Celery worker + Beat
- Vercel: Next.js frontend

**Render env (required for cross-origin auth):**

```env
ENVIRONMENT=production
FRONTEND_URL=https://analytics-platform-bay.vercel.app
BACKEND_CORS_ORIGINS=["https://analytics-platform-bay.vercel.app"]
```

**Vercel env:**

```env
NEXT_PUBLIC_API_BASE_URL=https://analytics-platform-2-kpih.onrender.com/api/v1
NEXT_PUBLIC_WS_BASE_URL=wss://analytics-platform-2-kpih.onrender.com/api/v1
```

---

## Project layout

```text
backend/
  alembic/              # migrations
  app/api/v1/           # REST + WebSocket
  app/services/         # rate limit, cache, alerts, realtime
  scripts/              # start.sh, smoke_test_live.py
  tests/
frontend/
  app/workspace/        # ingestion, dashboards, alerts, team
render.yaml
REQUIREMENTS.md
SUBMISSION.md
```

---

## API highlights

- `POST /api/v1/auth/signup` · `POST /api/v1/auth/login` · `POST /api/v1/auth/refresh`
- `POST /api/v1/events` (header `X-API-Key`)
- `GET /api/v1/dashboards/{id}/data?hours=168`
- `GET/POST /api/v1/alerts/`
- `WS /api/v1/realtime/events?token=...`
- `GET /health` · `GET /metrics`

---

## Tests

```powershell
cd backend
pytest tests -q
python scripts/smoke_test_live.py
```

---

## Environment

| File | Purpose |
|------|---------|
| `backend/.env.example` | Backend configuration |
| `frontend/.env.example` | Frontend API / WebSocket URLs |
