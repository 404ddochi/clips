# 운영 모니터링 (1차)

로컬 스크립트 + `/health` DB ping. **외부 알림(Discord, 이메일, UptimeRobot, Sentry)은 미구현.**

---

## 1. `/health`

`GET /health` — JSON only.

| HTTP | body | 의미 |
|------|------|------|
| 200 | `{"status":"ok","service":"CLIPS"}` | 앱 응답 + SQLAlchemy 세션으로 `SELECT 1` 성공 |
| 503 | `{"status":"degraded","service":"CLIPS"}` | DB 확인 실패 |

헤더: `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow` (+ 기존 security headers).

**노출하지 않는 것:** `environment`, 버전, 서버/DB 경로, 환경변수, 예외 메시지, traceback.  
실패 원인은 `logger.exception`으로 서버 로그에만 남긴다.

`robots.txt`: `Disallow: /health`. sitemap에 `/health` 없음.

```bash
curl -sf http://127.0.0.1:8000/health
```

---

## 2. `scripts/check_host.sh`

systemd 활성 여부, 로컬 health, 디스크/inode 사용률. **서비스를 재시작하거나 sudo를 쓰지 않음.**

```bash
chmod +x /var/www/clips/scripts/check_host.sh
/var/www/clips/scripts/check_host.sh
```

| 변수 | 기본 |
|------|------|
| `SERVICE_NAME` | `clips` |
| `HEALTH_URL` | `http://127.0.0.1:8000/health` |
| `DISK_PATH` | `/` |
| `DISK_WARN_PERCENT` / `DISK_CRITICAL_PERCENT` | 80 / 90 |
| `INODE_WARN_PERCENT` / `INODE_CRITICAL_PERCENT` | 80 / 90 |

| exit | 출력 |
|------|------|
| 0 | `OK ...` 또는 `WARN ...` (warn 임계치) |
| 1 | stderr에 `FAIL ...` (inactive, health, critical disk/inode) |

curl 타임아웃: connect 3s, max 5s. `jq` 불필요.

---

## 3. `scripts/check_backup_freshness.sh`

로컬 백업 디렉터리의 최신 `*.tar.gz`만 검사. Drive API 호출·백업 수정/삭제 없음. GNU coreutils (`stat -c`) 기준.

```bash
chmod +x /var/www/clips/scripts/check_backup_freshness.sh
/var/www/clips/scripts/check_backup_freshness.sh
```

| 변수 | 기본 |
|------|------|
| `BACKUP_DIR` | `/backup/clips` |
| `MAX_AGE_HOURS` | `26` |
| `MIN_SIZE_BYTES` | `1024` |
| `BACKUP_LOG_FILE` | `/var/log/clips-backup.log` |

성공 예: `OK backup=/backup/clips/....tar.gz age_hours=8 size_bytes=123456`  
로그 파일 없음 → stderr WARN, 아카이브 OK면 exit 0.  
로그에 `ERROR` / `FAILED` / `Backup failed` / `rclone failed` / `upload failed` → exit 1.

| exit | 의미 |
|------|------|
| 0 | 최신 백업 신선·크기·gzip OK |
| 1 | 디렉터리/아카이브 문제 또는 로그 실패 흔적 |

---

## 4. cron 예시 (등록은 운영자)

```cron
*/5 * * * * /var/www/clips/scripts/check_host.sh >> /var/log/clips-health.log 2>&1
30 5 * * * /var/www/clips/scripts/check_backup_freshness.sh >> /var/log/clips-backup-check.log 2>&1
```

cron 실패 시 메일/알림 연동은 아직 없음. 로그 파일을 주기적으로 확인한다.

관련: [backup-restore.md](backup-restore.md), [11-deployment-strategy.md](11-deployment-strategy.md) §15.
