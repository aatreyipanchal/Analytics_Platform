# Submission — AI Engineer Assessment

**Candidate project:** Pulseboard Analytics  
**Stack:** FastAPI · PostgreSQL · Celery · Redis · Next.js 14 · TypeScript

---

## Live demo (please start here)

| | URL |
|---|-----|
| **Application** | https://analytics-platform-bay.vercel.app/ |
| **API** | https://analytics-platform-2-kpih.onrender.com |
| **Swagger** | https://analytics-platform-2-kpih.onrender.com/docs |
| **Health** | https://analytics-platform-2-kpih.onrender.com/health |
| **Metrics** | https://analytics-platform-2-kpih.onrender.com/metrics |

**API base (all REST routes):** `https://analytics-platform-2-kpih.onrender.com/api/v1`  
**WebSocket base:** `wss://analytics-platform-2-kpih.onrender.com/api/v1`

### 3-minute evaluation path

1. Open https://analytics-platform-bay.vercel.app/ — sign up with any email (creates organization + Owner role).
2. **Ingestion** (https://analytics-platform-bay.vercel.app/workspace/ingestion) → create API key → submit the built-in sample event or upload `sample-events.csv`.
3. **Dashboards** (https://analytics-platform-bay.vercel.app/workspace/dashboards) → “Use template” (Web Analytics) or add a widget with event name `signup_completed`.
4. **Alerts** (https://analytics-platform-bay.vercel.app/workspace/alerts) → optional: create threshold on `error_logged`.
5. **Team** (https://analytics-platform-bay.vercel.app/workspace/team) → generate invite link.

Automated API smoke test against production (from repo root):

```bash
pip install httpx
python backend/scripts/smoke_test_live.py
```

The script hits `https://analytics-platform-2-kpih.onrender.com` (health, signup, login, dashboards, alerts). Override with `SMOKE_API_BASE` / `SMOKE_ROOT` if needed.

---

## Requirements coverage

See **[REQUIREMENTS.md](./REQUIREMENTS.md)** for a line-by-line matrix against the assessment brief (Must Have / Should Have / gaps).

**Summary:** All **Must Have** backend and core product flows are implemented and deployed. **Should Have** (alerts, WebSockets) included. Documented gaps: drag-and-drop widgets, saved-query entities, PDF scheduled reports, bonus items (GraphQL, OpenTelemetry, etc.).

---

## Architecture highlights

- Multi-tenant RBAC with JWT + HTTP-only refresh cookies  
- Async SQLAlchemy 2 + Alembic migrations  
- Celery workers + Beat for ingestion and alert evaluation  
- Redis for rate limits, dashboard cache, and WebSocket pub/sub  
- Structured logging with correlation IDs  
- Monorepo with Render blueprint + Vercel frontend  

**Production CORS (Render `pulseboard-api` / `analytics-platform-2-kpih`):**

```env
FRONTEND_URL=https://analytics-platform-bay.vercel.app
BACKEND_CORS_ORIGINS=["https://analytics-platform-bay.vercel.app"]
```

---

## Repository

- Setup: [README.md](./README.md)  
- Deploy: [DEPLOYMENT.md](./DEPLOYMENT.md)  
- CI: GitHub Actions (pytest + Next.js build)

---

## Known limitations (intentional scope)

- Widget layout uses ordered positions, not drag-and-drop.
- No scheduled PDF/email report generation.
- Integration test suite is focused (unit + smoke); not full E2E Playwright.
- Render free tier may cold-start (~30s) on first request.

Thank you for reviewing.
