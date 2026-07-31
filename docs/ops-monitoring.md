# 운영 모니터링

로컬 점검 스크립트 + `/health` DB ping + Discord webhook 실패/복구 알림.

이메일 / UptimeRobot / Sentry는 **미구현**.

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

## 2. 점검 스크립트

### `scripts/check_host.sh`

systemd 활성 여부, 로컬 health, 디스크/inode 사용률. **재시작/sudo 없음.**

| 변수 | 기본 |
|------|------|
| `SERVICE_NAME` | `clips` |
| `HEALTH_URL` | `http://127.0.0.1:8000/health` |
| `DISK_PATH` | `/` |
| `DISK_WARN_PERCENT` / `DISK_CRITICAL_PERCENT` | 80 / 90 |
| `INODE_WARN_PERCENT` / `INODE_CRITICAL_PERCENT` | 80 / 90 |

| exit | 출력 |
|------|------|
| 0 | `OK ...` 또는 `WARN ...` |
| 1 | stderr `FAIL ...` |

### `scripts/check_backup_freshness.sh`

최신 `*.tar.gz` 신선도·크기·gzip. Drive API 호출·백업 수정 없음. GNU `stat -c` 기준.

| 변수 | 기본 |
|------|------|
| `BACKUP_DIR` | `/backup/clips` |
| `MAX_AGE_HOURS` | `26` |
| `MIN_SIZE_BYTES` | `1024` (cron 래퍼 기본은 **500**) |
| `BACKUP_LOG_FILE` | `/var/log/clips-backup.log` |

| exit | 의미 |
|------|------|
| 0 | 최신 백업 OK (로그 없으면 WARN만) |
| 1 | 아카이브/로그 실패 |

---

## 3. Discord 알림 (2차)

### 구성 요소

| 스크립트 | 역할 |
|----------|------|
| `notify_discord.sh` | webhook POST (`INFO`/`WARN`/`ERROR`/`RECOVERY`) |
| `run_monitor_check.sh` | 점검 실행 + 상태 파일 + cooldown/복구 알림 |
| `run_host_monitor.sh` | cron용 host 엔트리 |
| `run_backup_monitor.sh` | cron용 backup 엔트리 |

### Webhook URL 관리

1. Discord 채널 → 연동 → 웹후크 → URL 복사
2. **저장소·채팅·티켓에 URL을 붙이지 말 것**
3. 운영 서버에만 기록:

```bash
sudo cp /var/www/clips/config/clips-monitor.env.example /etc/clips-monitor.env
sudo chmod 600 /etc/clips-monitor.env
sudo chown root:root /etc/clips-monitor.env
sudo editor /etc/clips-monitor.env   # DISCORD_WEBHOOK_URL=...
```

예제: `config/clips-monitor.env.example` (값 비움).

| 권한 | 값 |
|------|-----|
| owner | `root:root` |
| mode | `600` |

URL이 로그·PR·스크린샷에 노출되면 **즉시 Discord에서 웹후크 삭제/재발급**.

스크립트는 webhook URL을 stdout/stderr에 출력하지 않는다. `set -x`로 cron을 돌리지 말 것.

### 상태 디렉터리

```bash
sudo mkdir -p /var/lib/clips-monitor
sudo chown root:root /var/lib/clips-monitor
sudo chmod 755 /var/lib/clips-monitor
```

체크별 상태 파일 예: `/var/lib/clips-monitor/host.state`

```
STATUS=OK|FAILED
LAST_ALERT_EPOCH=...
LAST_CHANGE_EPOCH=...
```

(파일을 `source` 하지 않음 — 키=값만 파싱.)

### 알림 규칙

| 이전 | 현재 | 동작 |
|------|------|------|
| OK / 없음 | 실패 | 즉시 `ERROR` |
| FAILED | 실패 | `ALERT_COOLDOWN_SECONDS`(기본 3600) 지나기 전 **생략**, 이후 재알림 |
| FAILED | 성공 | `RECOVERY` 1회 |
| OK | 성공 | 알림 없음 |

- 점검 실패 → 항상 exit 1 (Discord 전송 실패해도 성공으로 바꾸지 않음)
- 점검 성공 → exit 0 (복구 알림 실패해도 실패로 바꾸지 않음)

### 테스트 알림

```bash
sudo set -a; source /etc/clips-monitor.env; set +a
/var/www/clips/scripts/notify_discord.sh INFO "CLIPS monitor test" "manual test ping"
```

### 환경변수 (`/etc/clips-monitor.env`)

| 변수 | 기본 | 설명 |
|------|------|------|
| `DISCORD_WEBHOOK_URL` | (필수) | Discord webhook |
| `DISCORD_USERNAME` | `CLIPS Monitor` | 표시 이름 |
| `DISCORD_TIMEOUT_SECONDS` | `5` | curl max-time |
| `HOST_LABEL` | `production` | 메시지 Environment |
| `MONITOR_STATE_DIR` | `/var/lib/clips-monitor` | 상태 파일 |
| `ALERT_COOLDOWN_SECONDS` | `3600` | 동일 장애 재알림 간격 |

---

## 4. cron (등록은 운영자)

```cron
# host + Discord (매 5분)
*/5 * * * * /var/www/clips/scripts/run_host_monitor.sh >> /var/log/clips-health.log 2>&1

# 백업 생성 (매일 04:00) — 알림 래퍼와 별개
0 4 * * * /var/www/clips/scripts/backup.sh >> /var/log/clips-backup-cron.log 2>&1

# 백업 최신성 + Discord (매일 05:30)
30 5 * * * /var/www/clips/scripts/run_backup_monitor.sh >> /var/log/clips-backup-check.log 2>&1
```

`run_*_monitor.sh`는 `/etc/clips-monitor.env`만 source 한다.  
(`CLIPS_MONITOR_ENV`는 자동 테스트용 — 운영 cron에 넣지 말 것.)

관련: [backup-restore.md](backup-restore.md), [11-deployment-strategy.md](11-deployment-strategy.md) §15.
