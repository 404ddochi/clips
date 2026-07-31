#!/usr/bin/env bash
# Cron entrypoint: load monitor env and run backup freshness check with Discord alerts.
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/clips}"
# Production must use /etc/clips-monitor.env. CLIPS_MONITOR_ENV is for tests only.
ENV_FILE="${CLIPS_MONITOR_ENV:-/etc/clips-monitor.env}"

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

if [[ "${ENV_FILE}" != /* ]]; then
  fail "FAIL env_path_not_absolute"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  fail "FAIL missing_env path=${ENV_FILE}"
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

# Default size floor for ops freshness checks; env file / cron may override.
MIN_SIZE_BYTES="${MIN_SIZE_BYTES:-500}"
export MIN_SIZE_BYTES

exec "${PROJECT_DIR}/scripts/run_monitor_check.sh" backup \
  "${PROJECT_DIR}/scripts/check_backup_freshness.sh"
