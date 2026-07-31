#!/usr/bin/env bash
# Local host / service health check for CLIPS (read-only; no restarts).
set -Eeuo pipefail

SERVICE_NAME="${SERVICE_NAME:-clips}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
DISK_PATH="${DISK_PATH:-/}"
DISK_WARN_PERCENT="${DISK_WARN_PERCENT:-80}"
DISK_CRITICAL_PERCENT="${DISK_CRITICAL_PERCENT:-90}"
INODE_WARN_PERCENT="${INODE_WARN_PERCENT:-80}"
INODE_CRITICAL_PERCENT="${INODE_CRITICAL_PERCENT:-90}"

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

warn_msg=""
note_warn() {
  if [[ -z "${warn_msg}" ]]; then
    warn_msg="$*"
  else
    warn_msg="${warn_msg}; $*"
  fi
}

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    fail "FAIL missing_command cmd=${cmd}"
  fi
}

require_cmd systemctl
require_cmd curl
require_cmd df
require_cmd awk

active_state="$(systemctl is-active "${SERVICE_NAME}" 2>/dev/null || true)"
if [[ "${active_state}" != "active" ]]; then
  fail "FAIL service_inactive service=${SERVICE_NAME} state=${active_state:-unknown}"
fi

tmp_body="$(mktemp)"
trap 'rm -f "${tmp_body}"' EXIT

http_code="$(
  curl \
    --silent \
    --show-error \
    --connect-timeout 3 \
    --max-time 5 \
    --output "${tmp_body}" \
    --write-out '%{http_code}' \
    "${HEALTH_URL}" \
    || true
)"

if [[ -z "${http_code}" || "${http_code}" == "000" ]]; then
  fail "FAIL health_request_failed url=${HEALTH_URL}"
fi

if [[ "${http_code}" != "200" ]]; then
  fail "FAIL health_http_status url=${HEALTH_URL} code=${http_code}"
fi

body="$(tr -d '\n' <"${tmp_body}" | tr -s ' ')"
# Accept compact or spaced JSON: "status":"ok" / "status": "ok"
if ! printf '%s' "${body}" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"'; then
  fail "FAIL health_status_not_ok url=${HEALTH_URL}"
fi

disk_pct="$(
  df -P "${DISK_PATH}" | awk 'NR==2 { gsub(/%/,"",$5); print $5 }'
)"
inode_pct="$(
  df -Pi "${DISK_PATH}" | awk 'NR==2 { gsub(/%/,"",$5); print $5 }'
)"

if [[ -z "${disk_pct}" || ! "${disk_pct}" =~ ^[0-9]+$ ]]; then
  fail "FAIL disk_usage_unreadable path=${DISK_PATH}"
fi
if [[ -z "${inode_pct}" || ! "${inode_pct}" =~ ^[0-9]+$ ]]; then
  fail "FAIL inode_usage_unreadable path=${DISK_PATH}"
fi

if [[ "${disk_pct}" -ge "${DISK_CRITICAL_PERCENT}" ]]; then
  fail "FAIL disk_critical path=${DISK_PATH} used_percent=${disk_pct} critical=${DISK_CRITICAL_PERCENT}"
fi
if [[ "${inode_pct}" -ge "${INODE_CRITICAL_PERCENT}" ]]; then
  fail "FAIL inode_critical path=${DISK_PATH} used_percent=${inode_pct} critical=${INODE_CRITICAL_PERCENT}"
fi

if [[ "${disk_pct}" -ge "${DISK_WARN_PERCENT}" ]]; then
  note_warn "disk_warn path=${DISK_PATH} used_percent=${disk_pct} warn=${DISK_WARN_PERCENT}"
fi
if [[ "${inode_pct}" -ge "${INODE_WARN_PERCENT}" ]]; then
  note_warn "inode_warn path=${DISK_PATH} used_percent=${inode_pct} warn=${INODE_WARN_PERCENT}"
fi

if [[ -n "${warn_msg}" ]]; then
  printf 'WARN service=%s health=ok disk=%s%% inodes=%s%% %s\n' \
    "${SERVICE_NAME}" "${disk_pct}" "${inode_pct}" "${warn_msg}"
  exit 0
fi

printf 'OK service=%s health=ok disk=%s%% inodes=%s%%\n' \
  "${SERVICE_NAME}" "${disk_pct}" "${inode_pct}"
exit 0
