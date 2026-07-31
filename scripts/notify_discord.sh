#!/usr/bin/env bash
# Post a CLIPS monitor alert to Discord via webhook.
# Does not print the webhook URL. No Python/jq required.
set -Eeuo pipefail

LEVEL="${1:-}"
TITLE="${2:-}"
MESSAGE="${3:-}"

DISCORD_USERNAME="${DISCORD_USERNAME:-CLIPS Monitor}"
DISCORD_TIMEOUT_SECONDS="${DISCORD_TIMEOUT_SECONDS:-5}"
HOST_LABEL="${HOST_LABEL:-production}"

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

if [[ -z "${LEVEL}" || -z "${TITLE}" ]]; then
  fail "FAIL usage: notify_discord.sh <LEVEL> <TITLE> <MESSAGE>"
fi

case "${LEVEL}" in
  INFO|WARN|ERROR|RECOVERY) ;;
  *) fail "FAIL invalid_level level=${LEVEL}" ;;
esac

if [[ -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
  fail "FAIL missing_discord_webhook_url"
fi

# Escape a string for inclusion inside a JSON double-quoted value.
# Backslashes must be replaced first. Callers should strip other controls.
json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "${s}"
}

hostname_short="$(hostname -s 2>/dev/null || hostname 2>/dev/null || printf 'unknown')"
timestamp="$(TZ="${TZ:-Asia/Seoul}" date '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || date '+%Y-%m-%d %H:%M:%S %Z')"

content="$(
  printf '[%s] %s\n\nHost: %s\nEnvironment: %s\nTime: %s\nMessage: %s' \
    "${LEVEL}" \
    "${TITLE}" \
    "${hostname_short}" \
    "${HOST_LABEL}" \
    "${timestamp}" \
    "${MESSAGE}"
)"

# Discord content hard limit is 2000; keep a safety margin.
if ((${#content} > 1900)); then
  content="${content:0:1890}… truncated"
fi

escaped_content="$(json_escape "${content}")"
escaped_username="$(json_escape "${DISCORD_USERNAME}")"
payload="$(printf '{"username":"%s","content":"%s"}' "${escaped_username}" "${escaped_content}")"

tmp_body="$(mktemp)"
trap 'rm -f "${tmp_body}"' EXIT

http_code="$(
  curl \
    --silent \
    --show-error \
    --connect-timeout 3 \
    --max-time "${DISCORD_TIMEOUT_SECONDS}" \
    --request POST \
    --header 'Content-Type: application/json' \
    --data "${payload}" \
    --output "${tmp_body}" \
    --write-out '%{http_code}' \
    -- \
    "${DISCORD_WEBHOOK_URL}" \
    || true
)"

if [[ -z "${http_code}" || "${http_code}" == "000" ]]; then
  fail "FAIL discord_request_failed"
fi

if [[ ! "${http_code}" =~ ^2[0-9][0-9]$ ]]; then
  fail "FAIL discord_http_status code=${http_code}"
fi

printf 'OK discord_notified level=%s\n' "${LEVEL}"
exit 0
