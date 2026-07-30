#!/usr/bin/env bash
# CLIPS backup — clips.db, uploads/ (optional), .env
# Production defaults; override APP_ROOT / BACKUP_DIR / LOG_FILE for local tests.
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME

# Prefer short names; CLIPS_* kept for backward compatibility.
APP_ROOT="${APP_ROOT:-${CLIPS_APP_ROOT:-/var/www/clips}}"
BACKUP_DIR="${BACKUP_DIR:-${CLIPS_BACKUP_DIR:-/backup/clips}}"
LOG_FILE="${LOG_FILE:-${CLIPS_BACKUP_LOG:-/var/log/clips-backup.log}}"
RETENTION_DAYS="${RETENTION_DAYS:-${CLIPS_BACKUP_RETENTION_DAYS:-30}}"
DB_NAME="${DB_NAME:-${CLIPS_DB_NAME:-clips.db}}"

readonly APP_ROOT BACKUP_DIR LOG_FILE RETENTION_DAYS DB_NAME

STAGING_DIR=""
LOG_CAN_WRITE=0

log() {
  local level="$1"
  shift
  local msg="$*"
  local ts line
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  line="[${ts}] [${level}] ${msg}"
  # Always print to the console (INFO/WARN → stdout, ERROR → stderr).
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
  if [[ -n "${STAGING_DIR}" && -d "${STAGING_DIR}" ]]; then
    rm -rf "${STAGING_DIR}"
  fi
}

on_error() {
  local exit_code=$?
  local line_no="${1:-unknown}"
  # Never let logging itself abort the error handler.
  log "ERROR" "Backup failed (exit=${exit_code}) at ${SCRIPT_NAME}:${line_no}" || true
  cleanup || true
  exit "${exit_code}"
}

trap 'on_error $LINENO' ERR
trap cleanup EXIT

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    log "ERROR" "Required command not found: ${cmd}"
    exit 1
  fi
}

human_size() {
  local bytes="$1"
  if command -v numfmt >/dev/null 2>&1; then
    numfmt --to=iec --suffix=B "${bytes}"
  else
    printf '%sB' "${bytes}"
  fi
}

file_size_bytes() {
  local path="$1"
  # Portable byte size (macOS/Linux).
  if stat -f%z "${path}" >/dev/null 2>&1; then
    stat -f%z "${path}"
  else
    stat -c%s "${path}"
  fi
}

purge_old_backups() {
  local old
  # BSD and GNU find both support -mtime +N.
  while IFS= read -r old; do
    [[ -z "${old}" ]] && continue
    rm -f "${old}"
    log "INFO" "Deleted expired backup: ${old}"
  done < <(find "${BACKUP_DIR}" -type f -name '*.tar.gz' -mtime "+${RETENTION_DAYS}" 2>/dev/null || true)
}

main() {
  init_logging

  require_cmd tar
  require_cmd sqlite3
  require_cmd date
  require_cmd mktemp
  require_cmd find

  if [[ ! -d "${APP_ROOT}" ]]; then
    log "ERROR" "APP_ROOT does not exist: ${APP_ROOT}"
    exit 1
  fi

  local db_path="${APP_ROOT}/${DB_NAME}"
  local uploads_path="${APP_ROOT}/uploads"
  local env_path="${APP_ROOT}/.env"

  if [[ ! -f "${db_path}" ]]; then
    log "ERROR" "Database file not found: ${db_path}"
    exit 1
  fi
  if [[ ! -f "${env_path}" ]]; then
    log "ERROR" ".env not found: ${env_path}"
    exit 1
  fi

  local have_uploads=0
  if [[ -d "${uploads_path}" ]]; then
    have_uploads=1
  else
    log "WARN" "uploads/ missing — continuing with empty uploads in archive"
  fi

  log "INFO" "Integrity check: ${db_path}"
  local integrity
  integrity="$(sqlite3 "${db_path}" "PRAGMA integrity_check;")"
  if [[ "${integrity}" != "ok" ]]; then
    log "ERROR" "sqlite integrity_check failed: ${integrity}"
    exit 1
  fi
  log "INFO" "sqlite integrity_check: ok"

  if ! mkdir -p "${BACKUP_DIR}"; then
    log "ERROR" "Cannot create BACKUP_DIR: ${BACKUP_DIR}"
    exit 1
  fi
  chmod 700 "${BACKUP_DIR}" 2>/dev/null || true

  local stamp archive_name archive_path
  stamp="$(date '+%Y-%m-%d_%H%M%S')"
  archive_name="${stamp}.tar.gz"
  archive_path="${BACKUP_DIR}/${archive_name}"

  STAGING_DIR="$(mktemp -d "${TMPDIR:-/tmp}/clips-backup.XXXXXX")"
  mkdir -p "${STAGING_DIR}/clips-backup/uploads"

  cp -a "${db_path}" "${STAGING_DIR}/clips-backup/${DB_NAME}"
  cp -a "${env_path}" "${STAGING_DIR}/clips-backup/.env"

  if [[ "${have_uploads}" -eq 1 ]]; then
    tar \
      --exclude='.git' \
      --exclude='.venv' \
      --exclude='__pycache__' \
      --exclude='.pytest_cache' \
      --exclude='.mypy_cache' \
      --exclude='.ruff_cache' \
      --exclude='node_modules' \
      -C "${uploads_path}" \
      -cf - \
      . \
      | tar -C "${STAGING_DIR}/clips-backup/uploads" -xf -
  fi

  tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='.ruff_cache' \
    --exclude='node_modules' \
    -C "${STAGING_DIR}" \
    -czf "${archive_path}.partial" \
    clips-backup

  mv "${archive_path}.partial" "${archive_path}"
  chmod 600 "${archive_path}" 2>/dev/null || true

  local bytes size_h
  bytes="$(file_size_bytes "${archive_path}")"
  size_h="$(human_size "${bytes}")"

  log "INFO" "Backup success time=$(date '+%Y-%m-%d %H:%M:%S') file=${archive_name} size=${size_h} (${bytes} bytes) path=${archive_path}"

  purge_old_backups

  cleanup
  trap - EXIT
}

main "$@"
