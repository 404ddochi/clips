#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "가상환경이 활성화되어 있지 않습니다."
  echo "  python3 -m venv .venv && source .venv/bin/activate"
  exit 1
fi

exec uvicorn app.main:app --reload --host "${APP_HOST:-127.0.0.1}" --port "${APP_PORT:-8000}"
