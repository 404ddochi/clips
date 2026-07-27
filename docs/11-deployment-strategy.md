# 11. 배포 전략

CLIPS 운영 배포는 **Ubuntu + Nginx + systemd + Git pull** 기반을 전제로 한다. 본 문서는 **실제 서버 IP·도메인·비밀값을 기록하지 않으며**, 역할·절차·롤백만 정의한다.

**범례:** **확정** / **향후 결정**

---

## 1. 목표

### 확정

- **단일 VM** 또는 소규모 1-app + 1-DB 구성으로 시작
- **HTTPS** 필수, HTTP → HTTPS redirect
- 배포 시 **짧은 다운타임** 허용; 무중단은 2차 목표
- 설정·코드·DB 스키마 변경 추적 가능

### 향후 결정

- Blue/green, second instance behind load balancer
- Container (Docker) vs bare metal

---

## 2. 서버 OS

### 확정

- **Ubuntu LTS** (22.04 또는 24.04)
- timezone: **Asia/Seoul**
- locale: `en_US.UTF-8` + 앱 `TIMEZONE=Asia/Seoul`
- 전용 Unix user `clips` (non-root app run)

### 향후 결정

- unattended-upgrades security only

---

## 3. Nginx

### 확정

- 역할: TLS termination, static cache, gzip/brotli, rate limit, reverse proxy → Uvicorn `127.0.0.1:8000`
- `client_max_body_size` — upload 5MB + margin (**6m**)
- `/static/` — `alias` + long cache `Cache-Control: public, max-age=31536000, immutable` (파일명 버전 **향후** hash)
- `/admin/login` — `limit_req` ([09-security-strategy.md](09-security-strategy.md))
- proxy headers: `Host`, `X-Forwarded-Proto`, `X-Real-IP` — **trusted hop only**

### 향후 결정

- brotli module
- separate admin subdomain

---

## 4. systemd

### 확정

- Unit: `clips.service`
- User=`clips`, WorkingDirectory=`/var/www/clips` (예시 경로)
- ExecStart: `/var/www/clips/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2`
- `Restart=on-failure`, `EnvironmentFile=/var/www/clips/.env`
- `After=network.target postgresql.service` (PostgreSQL 사용 시)

### 향후 결정

- workers 수 = CPU*2+1 rule vs 2 fixed
- journald log rotation

---

## 5. Git 기반 배포

### 확정

- 서버 clone: **read-only deploy key** 또는 CI artifact
- 브랜치: `main` (또는 `production`) — **향후 결정** naming
- 배포 스크립트 `scripts/deploy.sh` (**향후** 작성):

```bash
# 개념적 순서 (실제 IP/경로 미포함)
git fetch && git checkout <tag-or-commit>
source .venv/bin/activate
pip install -e ".[dev]"  # 또는 production extra only
alembic upgrade head
sudo systemctl reload nginx   # 설정 변경 시
sudo systemctl restart clips
curl -sf http://127.0.0.1:8000/health
```

- **태그** `vYYYY.MM.DD-N` 또는 semver — rollback anchor

### 향후 결정

- GitHub Actions SSH deploy
- immutable artifact (wheel + static tarball)

---

## 6. 환경변수

### 확정

- 경로: `/var/www/clips/.env`, mode **600**, owner `clips`
- 필수: `APP_ENV=production`, `APP_DEBUG=false`, `SECRET_KEY`, `DATABASE_URL`, `APP_BASE_URL=https://<your-domain>`
- `.env` never in Git

### 향후 결정

- systemd drop-in overrides per staging

---

## 7. 데이터베이스 마이그레이션

### 확정

- **Alembic** `upgrade head` **배포 restart 전**
- backward-compatible migrate (**expand → deploy → contract** for zero-downtime column drops — **향후**)
- SQLite(prod) **비권장** — PostgreSQL **확정** 운영 방향
- backup **before migrate** on prod

### 향후 결정

- migrate 실패 auto rollback script

---

## 8. 정적 파일 캐시

### 확정

- Nginx serves `app/static/` directly
- CSS/JS 변경 시 cache bust: query `?v=` or filename hash — **향후 결정** one strategy
- HTML: **no cache** or short cache (SSR dynamic)

---

## 9. HTTPS

### 확정

- **Let's Encrypt** certbot + nginx plugin
- auto renew cron/systemd timer
- HSTS after stable HTTPS ([09-security-strategy.md](09-security-strategy.md))

### 향후 결정

- wildcard cert

---

## 10. 로그

### 확정

- app → stdout → **journald** (`journalctl -u clips`)
- Nginx access/error: `/var/log/nginx/`
- logrotate default
- **no secrets** in logs ([09-security-strategy.md](09-security-strategy.md))

### 향후 결정

- Loki/CloudWatch ship
- request id middleware

---

## 11. 백업

### 확정

- DB: daily `pg_dump` (custom format) → encrypted off-site
- retention: **14일** minimum (**향후** 30)
- `.env` **별도** secret backup (password manager)
- uploads/ periodic rsync (**배너 도입 후**)

### 향후 결정

- restore runbook automation

---

## 12. 롤백 (rollback)

### 확정

1. `git checkout <previous-tag>`
2. `pip install` if deps changed
3. **DB downgrade** only if migrate reversible — otherwise forward-fix
4. `systemctl restart clips`
5. verify `/health`, smoke home
6. incident note in audit/changelog

### 향후 결정

- keep last 3 releases on disk

---

## 13. 무중단 / 최소 중단

### 확정 (초기)

- **허용:** restart 1~3초 502 window
- 순서: migrate → restart single worker gradually **불가** (single instance) → simple restart

### 향후 결정

- 2 instances + rolling reload
- `SO_REUSEPORT` / connection draining

---

## 14. 스테이징

### 향후 결정

- staging subdomain, robots noindex
- prod-like PostgreSQL version

### 확정

- local → staging → prod promote manual until CI mature

---

## 15. 모니터링

### 확정

- external uptime: `/health` every 1–5 min
- disk space alert

### 향후 결정

- Sentry, Prometheus node_exporter

---

## 16. 방화벽

### 확정

- ufw: allow 22 (restrict source **향후**), 80, 443
- PostgreSQL **localhost only**

---

## 17. 배포 체크리스트 연동

- [10-testing-strategy.md](10-testing-strategy.md) §15
- [09-security-strategy.md](09-security-strategy.md) production settings

---

## 18. 디렉터리 레이아웃 (예시)

```
/var/www/clips/          # app root, owner clips
/var/www/clips/.venv/
/var/www/clips/.env      # 600
/var/backups/clips/      # pg dumps
```

**실제 IP·호스트명은 문서에 기록하지 않는다.**

---

## 변경 이력

| 날짜 | 요약 |
|------|------|
| 2026-07-27 | 초안 작성 |
