# Pulseboard Analytics

Pulseboard is a multi-tenant analytics workspace built for the Senior Full Stack Engineer assessment. It provides:

- FastAPI + SQLAlchemy 2.0 async backend
- PostgreSQL for application and event data
- Celery + Redis for async ingestion processing
- Next.js 14 frontend for auth, team onboarding, ingestion, and dashboards

## Implemented Scope

### Backend

- Email/password signup and login
- JWT access token + refresh token cookie
- Organization creation during signup
- Invite-based onboarding
- Role hierarchy: `Owner`, `Admin`, `Analyst`, `Viewer`
- Organization-scoped data access
- API key creation, rotation, and revocation
- Event ingestion endpoints:
  - single event
  - batch events
  - CSV upload
  - webhook-style JSON ingestion
- Rate limiting on ingestion
- Async event processing through Celery
- Dashboard creation
- Dashboard templates
- Widget creation
- Widget data for `line`, `bar`, `pie`, `kpi`, and `table`
- Public dashboard read endpoint

### Frontend

- Signup / sign-in page
- Invite acceptance flow
- Workspace overview
- Ingestion page:
  - API key management
  - sample event submission
  - CSV upload
  - recent event stream
- Dashboards page:
  - create blank dashboard
  - create from template
  - add widgets
  - public/private toggle
- Team page:
  - invite teammates
  - review invite links and statuses

## Project Layout

```text
backend/
  app/
    api/
    core/
    models/
    repositories/
    schemas/
    workers/
  tests/
frontend/
  app/
  components/
  lib/
sample-events.csv
docker-compose.yml
```

## Environment Files

### Backend

Create `backend/.env` from `backend/.env.example`.

Example values for local Windows setup:

```env
PROJECT_NAME=Pulseboard Analytics
VERSION=0.2.0
API_V1_STR=/api/v1

SECRET_KEY=replace-with-a-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
INVITATION_TOKEN_EXPIRE_HOURS=72

POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=postgres1
POSTGRES_PORT=5432

REDIS_URL=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=true
AUTO_CREATE_TABLES=true

BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
FRONTEND_URL=http://localhost:3000
REFRESH_COOKIE_NAME=analytics_refresh_token
REFRESH_COOKIE_SECURE=false

DEFAULT_DASHBOARD_REFRESH_SECONDS=60
RATE_LIMIT_PER_MINUTE=240
```

Notes:

- If your PostgreSQL password contains `@`, the app now handles it correctly.
- `POSTGRES_DB` should match the database you want to use, for example `postgres1`.
- Redis on Windows can run through Memurai on `localhost:6379`.

### Frontend

Create `frontend/.env.local` from `frontend/.env.example`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Local Run

### Prerequisites

- Python virtual environment already set up at `venv`
- PostgreSQL running on `localhost:5432`
- Redis or Memurai running on `localhost:6379`
- Node.js / npm installed

### 1. Start backend API

From PowerShell:

```powershell
cd D:\Projects\AI_Assignment\backend
D:\Projects\AI_Assignment\venv\Scripts\Activate.ps1
..\venv\Scripts\uvicorn.exe app.main:app --reload
```

Backend will be available at:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 2. Start Celery worker

In a second PowerShell window:

```powershell
cd D:\Projects\AI_Assignment\backend
D:\Projects\AI_Assignment\venv\Scripts\Activate.ps1
..\venv\Scripts\celery.exe -A app.workers.celery_app worker --loglevel=info
```

### 3. Start frontend

In a third PowerShell window:

```powershell
cd D:\Projects\AI_Assignment\frontend
npm run dev
```

Frontend will be available at:

- `http://localhost:3000`

## How To Use The App

### 1. Create workspace or sign in

- Open `http://localhost:3000`
- Create an organization or sign in with an existing user

### 2. Ingest data

- Open `Workspace -> Ingestion`
- Create an API key
- Copy the full secret shown after creation
- Paste it into the `Current ingestion secret` field
- Either:
  - submit the sample event from the page
  - upload `sample-events.csv`

### 3. Build dashboards

- Open `Workspace -> Dashboards`
- Create a blank dashboard or use a template
- Add widgets using event names you have ingested

Examples:

- `signup_completed`
- `page_view`
- `purchase_completed`
- `error_logged`

You will start seeing KPI / chart data when:

- events have been ingested successfully
- widget `event_name` matches those events
- the selected time range includes those timestamps

### 4. Invite teammates

- Open `Workspace -> Team`
- Enter teammate email and role
- Click `Invite`
- Copy the generated invite link
- Send it to the teammate

Teammate flow:

- open the invite link
- set a password
- they join the same organization
- they can sign in and use the app according to their assigned role

## CSV Format

You can upload the provided file:

- [sample-events.csv](D:\Projects\AI_Assignment\sample-events.csv)

Required CSV columns:

```csv
event_name,timestamp,user_id,properties
```

Rules:

- `event_name`: non-empty text
- `timestamp`: ISO datetime
- `user_id`: text
- `properties`: JSON object encoded as a string

Example:

```csv
event_name,timestamp,user_id,properties
signup_completed,2026-05-20T10:30:00+00:00,user_1,"{""source"":""landing-page"",""plan"":""pro""}"
page_view,2026-05-20T10:35:00+00:00,user_1,"{""path"":""/pricing""}"
purchase_completed,2026-05-20T10:40:00+00:00,user_1,"{""amount"":1200,""currency"":""USD""}"
```

## Useful API Paths

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/invitations`
- `GET /api/v1/auth/invitations`
- `POST /api/v1/auth/invitations/accept`
- `GET /api/v1/organizations/me`
- `GET /api/v1/organizations/api-keys`
- `POST /api/v1/organizations/api-keys`
- `POST /api/v1/organizations/api-keys/{api_key_id}/rotate`
- `DELETE /api/v1/organizations/api-keys/{api_key_id}`
- `POST /api/v1/events`
- `POST /api/v1/events/batch`
- `POST /api/v1/events/upload/csv`
- `POST /api/v1/events/webhook`
- `GET /api/v1/events/recent`
- `GET /api/v1/dashboards`
- `GET /api/v1/dashboards/templates`
- `POST /api/v1/dashboards`
- `POST /api/v1/dashboards/templates/{template_slug}`
- `PATCH /api/v1/dashboards/{dashboard_id}`
- `POST /api/v1/dashboards/{dashboard_id}/widgets`
- `GET /api/v1/dashboards/{dashboard_id}/data`
- `GET /api/v1/dashboards/public/{dashboard_id}`

## Tests

Run backend tests:

```powershell
cd D:\Projects\AI_Assignment\backend
..\venv\Scripts\pytest.exe tests -q
```

Result in this workspace during validation:

- `5 passed`

## Notes

- Alerts, scheduled reports, and real-time WebSocket updates are not fully implemented yet.
- The current implementation focuses on the assessment must-have flows: auth, org isolation, ingestion, API keys, invites, dashboards, and widget analytics.
