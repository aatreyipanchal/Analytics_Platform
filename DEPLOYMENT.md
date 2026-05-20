# Deployment Guide — Render (Backend) + Vercel (Frontend)

This guide deploys **Pulseboard Analytics** with:

| Component | Platform | Service name (blueprint) |
|-----------|----------|--------------------------|
| API | Render Web Service | `pulseboard-api` |
| Celery worker | Render Background Worker | `pulseboard-celery-worker` |
| Celery Beat | Render Background Worker | `pulseboard-celery-beat` |
| PostgreSQL | Render Postgres | `pulseboard-db` |
| Redis | Render Redis | `pulseboard-redis` |
| Frontend | Vercel | Next.js project |

---

## Prerequisites

- GitHub repository with this code pushed
- [Render](https://render.com) account
- [Vercel](https://vercel.com) account

---

## Part 1 — Deploy backend on Render

### Option A: Blueprint (recommended)

1. Push the repo to GitHub.
2. In Render: **New → Blueprint**.
3. Connect the repository and select `render.yaml` at the repo root.
4. Render creates: Postgres, Redis, API, Celery worker, Celery Beat.
5. After the API service is created, open **pulseboard-api → Environment** and set:

| Variable | Example |
|----------|---------|
| `FRONTEND_URL` | `https://your-app.vercel.app` |
| `BACKEND_CORS_ORIGINS` | `["https://your-app.vercel.app"]` |

Use JSON array syntax for `BACKEND_CORS_ORIGINS` (required for credentials/cookies).

6. Copy the API URL, e.g. `https://pulseboard-api.onrender.com`.

### Option B: Manual services

1. **PostgreSQL** — Create database, copy **Internal Database URL**.
2. **Redis** — Create Redis instance, copy connection string.
3. **Web Service** (Python):
   - Root directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `bash scripts/start.sh`
   - Env:
     ```
     ENVIRONMENT=production
     DATABASE_URL=<postgres-url>
     REDIS_URL=<redis-url>
     SECRET_KEY=<random-32+-chars>
     RUN_MIGRATIONS_ON_STARTUP=true
     AUTO_CREATE_TABLES=false
     CELERY_TASK_ALWAYS_EAGER=false
     FRONTEND_URL=https://your-app.vercel.app
     BACKEND_CORS_ORIGINS=["https://your-app.vercel.app"]
     ```
4. **Background Worker** — Root `backend`, start: `celery -A app.workers.celery_app worker --loglevel=info`, same `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`.
5. **Background Worker (Beat)** — Same env, start: `celery -A app.workers.celery_app beat --loglevel=info`.

### Verify backend

- Health: `GET https://<api-host>/health`
- Metrics: `GET https://<api-host>/metrics`
- Docs: `https://<api-host>/docs`

### Render notes

- Free tier services **spin down** after inactivity; first request may take ~30s.
- `DATABASE_URL` from Render uses `postgres://`; the app converts it to `postgresql+asyncpg://` automatically.
- Migrations run on API startup when `RUN_MIGRATIONS_ON_STARTUP=true`.

---

## Part 2 — Deploy frontend on Vercel

1. Import the GitHub repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Framework preset: **Next.js** (auto-detected).
4. Environment variables:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://pulseboard-api.onrender.com/api/v1` |
| `NEXT_PUBLIC_WS_BASE_URL` | `wss://pulseboard-api.onrender.com/api/v1` |

5. Deploy.

### Cross-origin auth (refresh cookie)

Production uses:

- `REFRESH_COOKIE_SECURE=true`
- `REFRESH_COOKIE_SAMESITE=none`

The frontend calls the API with `credentials: "include"`. Ensure `BACKEND_CORS_ORIGINS` on Render lists **only** your exact Vercel URL (no trailing slash).

After Vercel deploy, update Render `FRONTEND_URL` and `BACKEND_CORS_ORIGINS` if the URL changed, then **Manual Deploy** the API service.

---

## Part 3 — Smoke test production

1. Open `https://your-app.vercel.app`
2. Sign up → create organization
3. **Ingestion** → create API key → submit sample event
4. **Dashboards** → create dashboard + widget matching `signup_completed`
5. **Alerts** → create rule for `error_logged` threshold → ingest events → wait ~1 min for Beat

---

## Optional: Email alerts

On Render API + workers, add:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=app-password
SMTP_FROM_EMAIL=your@gmail.com
```

Set `notify_email` on alert rules in the UI.

---

## Local development (unchanged)

```powershell
# backend/.env — copy from backend/.env.example
CELERY_TASK_ALWAYS_EAGER=true
AUTO_CREATE_TABLES=true
ENVIRONMENT=development

# Terminal 1
cd backend
uvicorn app.main:app --reload

# Terminal 2 (optional if CELERY_TASK_ALWAYS_EAGER=false)
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3 (alerts)
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 4
cd frontend
npm run dev
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error on login | Add exact Vercel URL to `BACKEND_CORS_ORIGINS` |
| Refresh fails | Cookie needs HTTPS + `SameSite=None`; both sites must use HTTPS |
| Events not processing | Check Celery worker logs on Render |
| Alerts never fire | Ensure Beat worker is running; check `error_logged` event count |
| WebSocket disconnects | Render supports WS; confirm `NEXT_PUBLIC_WS_BASE_URL` uses `wss://` |
| DB connection errors | Use Render internal DB URL for workers in same region |

---

## CI

GitHub Actions runs backend tests on push (see `.github/workflows/ci.yml`).
