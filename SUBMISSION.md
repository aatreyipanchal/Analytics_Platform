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

### 3-minute evaluation path

1. Sign up with any email (creates organization + Owner role).
2. **Ingestion** → create API key → submit the built-in sample event or upload `sample-events.csv`.
3. **Dashboards** → “Use template” (Web Analytics) or add a widget with event name `signup_completed`.
4. **Alerts** → optional: create threshold on `error_logged`.
5. **Team** → generate invite link.

Automated API smoke test (from repo root):

```bash
pip install httpx
python backend/scripts/smoke_test_live.py
```

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
