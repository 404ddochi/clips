# CLIPS 운영 백업 · 복구

운영 서버에서 `clips.db`, `uploads/`, `.env`를 주기적으로 백업하고,
장애·삭제 사고 시 동일 구성으로 복구하기 위한 절차다.

**비밀값(`.env` 내용)은 로그에 기록하지 않는다.**

---

## 1. 기본 경로 · 환경변수

| 항목 | 기본값(운영) | 환경변수 |
|------|--------------|----------|
| 앱 루트 | `/var/www/clips` | `APP_ROOT` |
| 백업 디렉터리 | `/backup/clips` | `BACKUP_DIR` |
| 로그 | `/var/log/clips-backup.log` | `LOG_FILE` |
| systemd 유닛 | `clips` | `SERVICE_NAME` |
| 보관 일수 | `30` | `RETENTION_DAYS` |
| DB 파일명 | `clips.db` | `DB_NAME` |
| 서비스 제어 생략 | `false` | `BACKUP_SKIP_SERVICE_CONTROL` |
| rclone 업로드 | `true` | `RCLONE_ENABLED` |
| rclone remote | `gdrive` | `RCLONE_REMOTE` |
| Drive 폴더 | `CLIPS-Backup` | `RCLONE_DESTINATION` |
| rclone dry-run | `false` | `RCLONE_DRY_RUN` |

하위 호환: `CLIPS_APP_ROOT`, `CLIPS_BACKUP_DIR`, `CLIPS_BACKUP_LOG`,
`CLIPS_SERVICE_NAME`, `CLIPS_BACKUP_RETENTION_DAYS`, `CLIPS_DB_NAME`도 인식한다
(`APP_ROOT` 등 짧은 이름이 우선).

스크립트:

- `scripts/backup.sh` — systemctl 호출 없음
- `scripts/restore.sh` — 기본은 `systemctl stop/start`; 로컬은 `BACKUP_SKIP_SERVICE_CONTROL=true`

로그:

- `LOG_FILE` 상위 디렉터리 생성 시도
- 쓰기가 불가능하면 stderr에 안내하고 **콘솔만** 사용 (스크립트는 계속 진행 가능)
- 파일에 쓸 수 있을 때만 파일에도 기록; 항상 콘솔 출력

---

## 2. 백업 대상

필수:

- `clips.db`
- `.env`

선택:

- `uploads/` — 없으면 경고만 남기고 빈 `uploads/`로 아카이브 계속

압축 시 제외:

- `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `node_modules`

아카이브 내부:

```text
clips-backup/
  clips.db
  .env
  uploads/
```

파일명: `YYYY-MM-DD_HHMMSS.tar.gz`

---

## 3. 운영 백업

### 사전 조건

- `sqlite3`, `tar` 설치
- `APP_ROOT`에 `clips.db`, `.env` 존재
- `BACKUP_DIR` 쓰기 권한 (보통 root)

### 수동 실행

```bash
sudo chmod +x /var/www/clips/scripts/backup.sh
sudo /var/www/clips/scripts/backup.sh
```

### 무결성 검사

백업 전 `PRAGMA integrity_check;`가 `ok`일 때만 진행한다.

### 성공 로그 예

```text
[2026-07-30 04:00:01] [INFO] Backup success time=... file=2026-07-30_040001.tar.gz size=... path=/backup/clips/...
```

---

## 4. 보관 정책 · Google Drive

### 로컬

- 기본 **30일** (`RETENTION_DAYS`) 지난 `*.tar.gz` 삭제
- `/backup/clips` 권한 `700`, 아카이브 `600` 권장

### Google Drive (rclone)

로컬 tar.gz 생성 성공 직후:

```bash
rclone copy "$BACKUP_FILE" "${RCLONE_REMOTE}:${RCLONE_DESTINATION}"
```

- **copy만** 사용 (`sync` / `move` / `purge` 금지)
- `RCLONE_ENABLED=false`이면 업로드 건너뛰고 로그만 남김
- 업로드 실패 시 **로컬 파일은 유지**, 스크립트는 실패 종료
- 원격 정리: `rclone delete` + `--min-age "${RETENTION_DAYS}d"` + `--include "*.tar.gz"`  
  (폴더 자체는 삭제하지 않음)
- `RCLONE_DRY_RUN=true`이면 copy/delete에 `--dry-run`

**계정 주의:** cron 실행 사용자와 rclone 설정 사용자가 같아야 한다 (보통 root).

```bash
# 수동 업로드 확인
sudo rclone copy /backup/clips/2026-07-30_040001.tar.gz gdrive:CLIPS-Backup
sudo rclone lsf gdrive:CLIPS-Backup

# dry-run
sudo RCLONE_DRY_RUN=true /var/www/clips/scripts/backup.sh

# 업로드 끄기
sudo RCLONE_ENABLED=false /var/www/clips/scripts/backup.sh
```

---

## 5. 운영 복구

```bash
sudo chmod +x /var/www/clips/scripts/restore.sh
sudo /var/www/clips/scripts/restore.sh /backup/clips/2026-07-30_040001.tar.gz
```

순서: 압축 해제 → `systemctl stop` → 안전 복사 → 복원 → `systemctl start` → active 확인.

복구 후:

```bash
systemctl status clips
curl -sf http://127.0.0.1:8000/health
```

---

## 6. cron (매일 04:00)

```cron
0 4 * * * /var/www/clips/scripts/backup.sh >>/var/log/clips-backup.log 2>&1
```

또는 `/etc/cron.d/clips-backup`:

```cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

0 4 * * * root /var/www/clips/scripts/backup.sh
```

---

## 7. 로컬 테스트

### 백업

프로젝트 루트 (`.local-backups/`는 `.gitignore`됨):

```bash
APP_ROOT="$PWD" \
BACKUP_DIR="$PWD/.local-backups" \
LOG_FILE="$PWD/.local-backups/backup.log" \
RETENTION_DAYS=30 \
RCLONE_ENABLED=false \
./scripts/backup.sh
```

### 복구 — 반드시 임시 디렉터리에서

> **경고:** `restore.sh`는 `APP_ROOT`의 실제 `clips.db` / `.env` / `uploads`를 덮어씁니다.  
> 개발 중인 프로젝트 루트를 `APP_ROOT`로 지정하지 마세요.

```bash
RESTORE_ROOT="$(mktemp -d /tmp/clips-restore-XXXXXX)"
APP_ROOT="$RESTORE_ROOT" \
BACKUP_SKIP_SERVICE_CONTROL=true \
LOG_FILE="$PWD/.local-backups/restore.log" \
./scripts/restore.sh "$PWD/.local-backups/백업파일명.tar.gz"
ls -la "$RESTORE_ROOT"
rm -rf "$RESTORE_ROOT"
```

`BACKUP_SKIP_SERVICE_CONTROL=true`이면 `systemctl`을 호출하지 않는다.

---

## 8. 주의사항

1. `.env`에 비밀값이 포함된다. 백업 디렉터리 권한을 최소화한다.
2. PostgreSQL을 쓰면 이 SQLite 백업만으로는 부족하다.
3. 운영 복구는 서비스 중단이 발생한다.
4. `integrity_check` 실패 시 백업을 만들지 않는다.
5. macOS / Linux 모두에서 동작하도록 GNU 전용 옵션을 최소화했다.

---

## 9. 예상 용량

초기에는 일일 tar.gz가 보통 **100KB ~ 수 MB**. `uploads` 증가에 따라 커진다.

---

## 변경 이력

| 날짜 | 요약 |
|------|------|
| 2026-07-31 | `backup.sh` / `restore.sh` 초안 |
| 2026-07-31 | 환경변수·로컬 테스트·안전한 로깅·uploads 선택 |
| 2026-07-31 | rclone Google Drive copy 업로드·원격 보존 정리 |
