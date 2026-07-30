#!/usr/bin/env bash
# CLIPS restore from scripts/backup.sh archives.
# Usage: ./restore.sh /path/to/YYYY-MM-DD_HHMMSS.tar.gz
#
# Local dry-run (no systemctl):
#   APP_ROOT=/tmp/clips-restore-target BACKUP_SKIP_SERVICE_CONTROL=true ./scripts/restore.sh archive.tar.gz
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME

APP_ROOT="${APP_ROOT:-${CLIPS_APP_ROOT:-/var/www/clips}}"
SERVICE_NAME="${SERVICE_NAME:-${CLIPS_SERVICE_NAME:-clips}}"
LOG_FILE="${LOG_FILE:-${CLIPS_BACKUP_LOG:-/var/log/clips-backup.log}}"
DB_NAME="${DB_NAME:-${CLIPS_DB_NAME:-clips.db}}"
BACKUP_SKIP_SERVICE_CONTROL="${BACKUP_SKIP_SERVICE_CONTROL:-false}"

readonly APP_ROOT SERVICE_NAME LOG_FILE DB_NAME

EXTRACT_DIR=""
SERVICE_STOPPED=0
LOG_CAN_WRITE=0

log() {
  local level="$1"
  shift
  local msg="$*"
  local ts line
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  line="[${ts}] [${level}] ${msg}"
  if [[ "${level}" == "ERROR" ]]; then
    printf '%s\n' "${line}" >&2
  else
    printf '%s\n' "${line}"
  fi
  if [[ "${LOG_CAN_WRITE}" -eq 1 ]]; then
    printf '%s\n' "${line}" >>"${LOG_FILE}" || true
  fi
}

init_logging() {
  local log_dir
  log_dir="$(dirname "${LOG_FILE}")"
  if ! mkdir -p "${log_dir}" 2>/dev/null; then
    printf '%s\n' "ERROR: cannot create log directory: ${log_dir}" >&2
    LOG_CAN_WRITE=0
    return 0
  fi
  if ! touch "${LOG_FILE}" 2>/dev/null; then
    printf '%s\n' "ERROR: cannot write log file: ${LOG_FILE}" >&2
    LOG_CAN_WRITE=0
    return 0
  fi
  LOG_CAN_WRITE=1
}

cleanup() {
  if [[ -n "${EXTRACT_DIR}" && -d "${EXTRACT_DIR}" ]]; then
    rm -rf "${EXTRACT_DIR}"
  fi
}

skip_service_control() {
  case "${BACKUP_SKIP_SERVICE_CONTROL}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

ensure_service_running() {
  if [[ "${SERVICE_STOPPED}" -ne 1 ]]; then
    return 0
  fi
  if skip_service_control; then
    SERVICE_STOPPED=0
    return 0
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl start "${SERVICE_NAME}" || true
    SERVICE_STOPPED=0
    log "WARN" "Attempted to restart ${SERVICE_NAME} after failure" || true
  fi
}

on_error() {
  local exit_code=$?
  local line_no="${1:-unknown}"
  log "ERROR" "Restore failed (exit=${exit_code}) at ${SCRIPT_NAME}:${line_no}" || true
  ensure_service_running || true
  cleanup || true
  exit "${exit_code}"
}

trap 'on_error $LINENO' ERR
trap cleanup EXIT

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} <backup.tar.gz>

Restores clips.db, uploads/, and .env into APP_ROOT (${APP_ROOT}).

Environment:
  APP_ROOT=${APP_ROOT}
  SERVICE_NAME=${SERVICE_NAME}
  LOG_FILE=${LOG_FILE}
  DB_NAME=${DB_NAME}
  BACKUP_SKIP_SERVICE_CONTROL=${BACKUP_SKIP_SERVICE_CONTROL}
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    log "ERROR" "Required command not found: ${cmd}"
    exit 1
  fi
}

main() {
  init_logging

  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi
  if [[ $# -ne 1 ]]; then
    usage >&2
    exit 1
  fi

  local archive="$1"
  if [[ ! -f "${archive}" ]]; then
    log "ERROR" "Backup archive not found: ${archive}"
    exit 1
  fi
  case "${archive}" in
    *.tar.gz|*.tgz) ;;
    *)
      log "ERROR" "Expected a .tar.gz archive: ${archive}"
      exit 1
      ;;
  esac

  require_cmd tar
  require_cmd mktemp
  if ! skip_service_control; then
    require_cmd systemctl
  fi

  if [[ ! -d "${APP_ROOT}" ]]; then
    log "ERROR" "APP_ROOT does not exist: ${APP_ROOT}"
    exit 1
  fi

  EXTRACT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/clips-restore.XXXXXX")"
  log "INFO" "Extracting ${archive}"
  tar -xzf "${archive}" -C "${EXTRACT_DIR}"

  local payload="${EXTRACT_DIR}/clips-backup"
  if [[ ! -d "${payload}" ]]; then
    if [[ -f "${EXTRACT_DIR}/${DB_NAME}" && -f "${EXTRACT_DIR}/.env" ]]; then
      payload="${EXTRACT_DIR}"
    else
      log "ERROR" "Archive layout invalid: missing clips-backup/ (or root ${DB_NAME}/.env)"
      exit 1
    fi
  fi

  if [[ ! -f "${payload}/${DB_NAME}" ]]; then
    log "ERROR" "Archive missing ${DB_NAME}"
    exit 1
  fi
  if [[ ! -f "${payload}/.env" ]]; then
    log "ERROR" "Archive missing .env"
    exit 1
  fi
  if [[ ! -d "${payload}/uploads" ]]; then
    log "WARN" "Archive missing uploads/ — restoring empty uploads directory"
    mkdir -p "${payload}/uploads"
  fi

  if skip_service_control; then
    log "INFO" "BACKUP_SKIP_SERVICE_CONTROL=true — skipping systemctl stop/start"
  else
    log "INFO" "Stopping service ${SERVICE_NAME}"
    systemctl stop "${SERVICE_NAME}"
    SERVICE_STOPPED=1
  fi

  local safety_stamp safety_dir
  safety_stamp="$(date '+%Y-%m-%d_%H%M%S')"
  safety_dir="${APP_ROOT}/.restore-safety-${safety_stamp}"
  mkdir -p "${safety_dir}"
  if [[ -f "${APP_ROOT}/${DB_NAME}" ]]; then
    cp -a "${APP_ROOT}/${DB_NAME}" "${safety_dir}/${DB_NAME}"
  fi
  if [[ -f "${APP_ROOT}/.env" ]]; then
    cp -a "${APP_ROOT}/.env" "${safety_dir}/.env"
  fi
  if [[ -d "${APP_ROOT}/uploads" ]]; then
    cp -a "${APP_ROOT}/uploads" "${safety_dir}/uploads"
  fi
  log "INFO" "Pre-restore safety copy: ${safety_dir}"

  cp -a "${payload}/${DB_NAME}" "${APP_ROOT}/${DB_NAME}"
  cp -a "${payload}/.env" "${APP_ROOT}/.env"
  rm -rf "${APP_ROOT}/uploads"
  cp -a "${payload}/uploads" "${APP_ROOT}/uploads"

  chmod 600 "${APP_ROOT}/.env" 2>/dev/null || true
  chmod 600 "${APP_ROOT}/${DB_NAME}" 2>/dev/null || true

  if skip_service_control; then
    log "INFO" "Restore complete (service control skipped). Archive=${archive}"
    printf '\n복구가 완료되었습니다. (systemctl 건너뜀)\n'
    printf '  앱 경로: %s\n' "${APP_ROOT}"
    printf '  안전 복사: %s\n' "${safety_dir}"
    printf '  (확인 후 안전 복사 디렉터리를 수동 삭제하세요.)\n\n'
  else
    log "INFO" "Starting service ${SERVICE_NAME}"
    systemctl start "${SERVICE_NAME}"
    SERVICE_STOPPED=0
    if systemctl is-active --quiet "${SERVICE_NAME}"; then
      log "INFO" "Restore complete. ${SERVICE_NAME} is active. Archive=${archive}"
      printf '\n복구가 완료되었습니다.\n'
      printf '  서비스: %s (active)\n' "${SERVICE_NAME}"
      printf '  앱 경로: %s\n' "${APP_ROOT}"
      printf '  안전 복사: %s\n' "${safety_dir}"
      printf '  (확인 후 안전 복사 디렉터리를 수동 삭제하세요.)\n\n'
    else
      log "ERROR" "Service ${SERVICE_NAME} failed to become active after restore"
      exit 1
    fi
  fi

  cleanup
  trap - EXIT
}

main "$@"
