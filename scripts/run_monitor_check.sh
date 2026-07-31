#!/usr/bin/env bash
# Run a monitor check, track OK/FAILED state, and notify Discord on change/cooldown.
# Usage: run_monitor_check.sh <CHECK_NAME> <CHECK_COMMAND...>
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTIFY_SCRIPT="${NOTIFY_DISCORD_SCRIPT:-${SCRIPT_DIR}/notify_discord.sh}"

MONITOR_STATE_DIR="${MONITOR_STATE_DIR:-/var/lib/clips-monitor}"
ALERT_COOLDOWN_SECONDS="${ALERT_COOLDOWN_SECONDS:-3600}"
HOST_LABEL="${HOST_LABEL:-production}"
MAX_MESSAGE_CHARS=1500

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

CHECK_NAME="${1:-}"
if [[ -z "${CHECK_NAME}" ]]; then
  fail "FAIL usage: run_monitor_check.sh <CHECK_NAME> <CHECK_COMMAND...>"
fi
shift

if [[ ! "${CHECK_NAME}" =~ ^[A-Za-z0-9_-]+$ ]]; then
  fail "FAIL invalid_check_name name=${CHECK_NAME}"
fi

if [[ "$#" -lt 1 ]]; then
  fail "FAIL usage: run_monitor_check.sh <CHECK_NAME> <CHECK_COMMAND...>"
fi

if ! command -v flock >/dev/null 2>&1; then
  fail "FAIL missing_command cmd=flock"
fi

mkdir -p "${MONITOR_STATE_DIR}"

state_file="${MONITOR_STATE_DIR}/${CHECK_NAME}.state"
lock_file="${MONITOR_STATE_DIR}/${CHECK_NAME}.lock"

exec 9>"${lock_file}"
if ! flock -n 9; then
  fail "FAIL lock_busy check=${CHECK_NAME}"
fi

STATUS="OK"
LAST_ALERT_EPOCH=0
LAST_CHANGE_EPOCH=0

if [[ -f "${state_file}" ]]; then
  while IFS= read -r line || [[ -n "${line}" ]]; do
    case "${line}" in
      STATUS=OK)
        STATUS="OK"
        ;;
      STATUS=FAILED)
        STATUS="FAILED"
        ;;
      LAST_ALERT_EPOCH=*)
        val="${line#LAST_ALERT_EPOCH=}"
        if [[ "${val}" =~ ^[0-9]+$ ]]; then
          LAST_ALERT_EPOCH="${val}"
        fi
        ;;
      LAST_CHANGE_EPOCH=*)
        val="${line#LAST_CHANGE_EPOCH=}"
        if [[ "${val}" =~ ^[0-9]+$ ]]; then
          LAST_CHANGE_EPOCH="${val}"
        fi
        ;;
      *)
        ;;
    esac
  done <"${state_file}"
fi

prev_status="${STATUS}"
now_epoch="$(date +%s)"

out_file="$(mktemp)"
err_file="$(mktemp)"
trap 'rm -f "${out_file}" "${err_file}"' EXIT

set +e
"$@" >"${out_file}" 2>"${err_file}"
check_rc=$?
set -e

cat "${out_file}"
cat "${err_file}" >&2

combined="$(cat "${out_file}"; printf '\n'; cat "${err_file}")"
# Drop control characters (keep tab/newline); limit length for Discord body.
sanitized="$(
  printf '%s' "${combined}" \
    | tr -d '\000-\010\013\014\016-\037\177' \
    | head -c "${MAX_MESSAGE_CHARS}"
)"
if ((${#combined} > MAX_MESSAGE_CHARS)); then
  sanitized="${sanitized}… truncated"
fi
# Never include webhook URL if somehow present in check output.
if [[ -n "${DISCORD_WEBHOOK_URL:-}" ]]; then
  sanitized="${sanitized//${DISCORD_WEBHOOK_URL}/[webhook-redacted]}"
fi

write_state() {
  local status="$1"
  local last_alert="$2"
  local last_change="$3"
  local tmp="${state_file}.tmp.$$"
  printf 'STATUS=%s\nLAST_ALERT_EPOCH=%s\nLAST_CHANGE_EPOCH=%s\n' \
    "${status}" "${last_alert}" "${last_change}" >"${tmp}"
  mv "${tmp}" "${state_file}"
}

notify() {
  local level="$1"
  local title="$2"
  local message="$3"
  # Isolate notify failure from set -e caller decisions.
  set +e
  "${NOTIFY_SCRIPT}" "${level}" "${title}" "${message}"
  local nrc=$?
  set -e
  return "${nrc}"
}

fail_title=""
recovery_title=""
case "${CHECK_NAME}" in
  host)
    fail_title="CLIPS host check failed"
    recovery_title="CLIPS host check recovered"
    ;;
  backup)
    fail_title="CLIPS backup check failed"
    recovery_title="CLIPS backup check recovered"
    ;;
  *)
    fail_title="CLIPS ${CHECK_NAME} check failed"
    recovery_title="CLIPS ${CHECK_NAME} check recovered"
    ;;
esac

if [[ "${check_rc}" -ne 0 ]]; then
  # Failure path: always exit 1; Discord must not flip this to success.
  should_alert=0
  if [[ "${prev_status}" != "FAILED" ]]; then
    should_alert=1
  else
    elapsed=$((now_epoch - LAST_ALERT_EPOCH))
    if [[ "${LAST_ALERT_EPOCH}" -eq 0 || "${elapsed}" -ge "${ALERT_COOLDOWN_SECONDS}" ]]; then
      should_alert=1
    fi
  fi

  new_alert_epoch="${LAST_ALERT_EPOCH}"
  new_change_epoch="${LAST_CHANGE_EPOCH}"
  if [[ "${prev_status}" != "FAILED" ]]; then
    new_change_epoch="${now_epoch}"
  fi

  if [[ "${should_alert}" -eq 1 ]]; then
    if notify ERROR "${fail_title}" "${sanitized}"; then
      new_alert_epoch="${now_epoch}"
    else
      printf 'WARN discord_notify_failed check=%s level=ERROR\n' "${CHECK_NAME}" >&2
    fi
  fi

  write_state "FAILED" "${new_alert_epoch}" "${new_change_epoch}"
  exit 1
fi

# Success path
if [[ "${prev_status}" == "FAILED" ]]; then
  new_alert_epoch="${LAST_ALERT_EPOCH}"
  if notify RECOVERY "${recovery_title}" "${sanitized}"; then
    new_alert_epoch="${now_epoch}"
  else
    printf 'WARN discord_notify_failed check=%s level=RECOVERY\n' "${CHECK_NAME}" >&2
  fi
  write_state "OK" "${new_alert_epoch}" "${now_epoch}"
  exit 0
fi

write_state "OK" "${LAST_ALERT_EPOCH}" "${LAST_CHANGE_EPOCH}"
exit 0
