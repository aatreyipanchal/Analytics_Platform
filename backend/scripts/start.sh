#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Starting Pulseboard API (ENVIRONMENT=${ENVIRONMENT:-development})"

if [ "${RENDER:-false}" = "true" ] || [ "${ENVIRONMENT:-development}" = "production" ]; then
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL is not set. Link pulseboard-db to this service in Render."
    exit 1
  fi
fi

if [ "${RUN_MIGRATIONS_ON_STARTUP:-true}" = "true" ]; then
  echo "Running database migrations..."
  attempt=1
  max_attempts=30
  until alembic upgrade head; do
    if [ "$attempt" -ge "$max_attempts" ]; then
      echo "ERROR: Migrations failed after ${max_attempts} attempts. Is Postgres Available?"
      exit 1
    fi
    echo "Database not ready (attempt ${attempt}/${max_attempts}), retrying in 5s..."
    attempt=$((attempt + 1))
    sleep 5
  done
  echo "Migrations complete."
fi

echo "Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
