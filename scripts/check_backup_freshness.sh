#!/usr/bin/env bash
# Check that the newest local CLIPS backup archive is fresh and intact.
# Does not modify/delete backups or call Google Drive.
set -Eeuo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backup/clips}"
MAX_AGE_HOURS="${MAX_AGE_HOURS:-26}"
MIN_SIZE_BYTES="${MIN_SIZE_BYTES:-1024}"
BACKUP_LOG_FILE="${BACKUP_LOG_FILE:-/var/log/clips-backup.log}"

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

warn() {
  printf '%s\n' "WARN $*" >&2
}

if [[ ! -d "${BACKUP_DIR}" ]]; then
  fail "FAIL backup_dir_missing path=${BACKUP_DIR}"
fi

shopt -s nullglob
archives=()
while IFS= read -r line; do
  [[ -n "${line}" ]] || continue
  archives+=("${line}")
done < <(printf '%s\n' "${BACKUP_DIR}"/*.tar.gz | LC_ALL=C sort)
shopt -u nullglob

if [[ "${#archives[@]}" -eq 0 ]]; then
  fail "FAIL no_tar_gz path=${BACKUP_DIR}"
fi

newest=""
newest_mtime=0
for candidate in "${archives[@]}"; do
  [[ -f "${candidate}" ]] || continue
  mtime="$(stat -c '%Y' "${candidate}")"
  if [[ "${mtime}" -ge "${newest_mtime}" ]]; then
    newest_mtime="${mtime}"
    newest="${candidate}"
  fi
done

if [[ -z "${newest}" ]]; then
  fail "FAIL no_readable_tar_gz path=${BACKUP_DIR}"
fi

now="$(date +%s)"
age_seconds=$((now - newest_mtime))
max_age_seconds=$((MAX_AGE_HOURS * 3600))
age_hours=$((age_seconds / 3600))

if [[ "${age_seconds}" -gt "${max_age_seconds}" ]]; then
  fail "FAIL backup_too_old file=${newest} age_hours=${age_hours} max_age_hours=${MAX_AGE_HOURS}"
fi

size_bytes="$(stat -c '%s' "${newest}")"
if [[ "${size_bytes}" -lt "${MIN_SIZE_BYTES}" ]]; then
  fail "FAIL backup_too_small file=${newest} size_bytes=${size_bytes} min_size_bytes=${MIN_SIZE_BYTES}"
fi

if ! gzip -t "${newest}" 2>/dev/null; then
  fail "FAIL backup_gzip_corrupt file=${newest}"
fi

if [[ ! -f "${BACKUP_LOG_FILE}" ]]; then
  warn "backup_log_missing path=${BACKUP_LOG_FILE}"
else
  # Scan a recent tail for failure markers (read-only).
  if tail -n 200 "${BACKUP_LOG_FILE}" 2>/dev/null \
    | grep -Eiq 'ERROR|FAILED|Backup failed|rclone failed|upload failed'; then
    fail "FAIL backup_log_errors path=${BACKUP_LOG_FILE}"
  fi
fi

printf 'OK backup=%s age_hours=%s size_bytes=%s\n' "${newest}" "${age_hours}" "${size_bytes}"
exit 0
