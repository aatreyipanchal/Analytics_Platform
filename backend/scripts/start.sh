#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${RUN_MIGRATIONS_ON_STARTUP:-true}" = "true" ]; then
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
