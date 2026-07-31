# 10. 테스트 전략

CLIPS는 FastAPI + Jinja SSR + (향후) DB·크롤·관리자를 **pytest** 중심으로 검증한다. 본 문서는 테스트 피라미드, 범위, CI·배포 전 게이트를 정의한다.

**범례:** **확정** / **향후 결정**

---

## 1. 목표

### 확정

- **회귀 방지:** 라우트·SEO·핵심 서비스 로직
- **보안 회귀:** CSRF, escape, upload 거부
- **배포 신뢰:** migrate + smoke + lint/typecheck
- 실네트워크·실공식 사이트 크롤 **CI 금지** (fixture/mock)

### 향후 결정

- 커버리지 gate (예: 70% services)
- Playwright E2E

---

## 2. 테스트 피라미드

```
        ┌─────────────┐
        │  E2E (소수) │  향후 Playwright
        ├─────────────┤
        │ 통합·라우트  │  httpx TestClient + DB
        ├─────────────┤
        │  단위 (다수) │  pure functions, services
        └─────────────┘
```

### 확정

- `tests/` + `conftest.py` — **TestClient**, **임시 SQLite** (in-memory 또는 tmp file)
- `./scripts/test.sh` = `pytest` (**확정**)

---

## 3. 단위 테스트 (unit)

### 확정

| 대상 | 예시 |
|------|------|
| `app/config.py` | production + default SECRET_KEY → RuntimeError |
| `app/services/seo.py` | canonical, absolute_url |
| crawl normalize | URL 정규화, date parse, content_hash |
| search utils | keyword normalize, snippet, highlight escape |
| password | verify hash roundtrip |

- **mock:** 외부 HTTP, clock, random UUID
- 파일명: `test_<module>.py`

### 향후 결정

- property-based (hypothesis) for parsers

---

## 4. 통합 테스트 (integration)

### 확정

- SQLAlchemy session + repository CRUD (posts, coupons)
- Alembic upgrade head on empty DB (**향후** CI job)
- crawl upsert: pinned/hidden/manual_override 보호
- transaction rollback per test (`conftest` fixture)

### 향후 결정

- Testcontainers PostgreSQL

---

## 5. 라우트 테스트 (route / API)

### 확정 (현재 + 확장)

| 라우트 | 검증 |
|--------|------|
| `GET /health` | 200 + `status=ok` + `service=CLIPS`; `environment` 미노출; `Cache-Control=no-store`; DB 실패 시 503 `degraded` (예외 미노출) |
| `GET /` | 200, H1×1, title, meta description |
| `GET /robots.txt` | 200, `Disallow: /health`, Sitemap uses site URL |
| `GET /sitemap.xml` | 200, valid urlset; `/health` 미포함 |
| `GET /unknown` | 404 HTML |

- `httpx.AsyncClient` 또는 Starlette `TestClient`
- `APP_ENV=test`, isolated settings override

### 향후 결정

- boards, search, coupons public routes

---

## 6. 템플릿 테스트

### 확정

- 응답 HTML parse (regex 또는 **selectolax**/BeautifulSoup in dev deps **향후**):
  - `lang="ko"`
  - header nav links exist
  - footer 비공식 고지
- **`| safe` 남용** grep + review checklist

### 향후 결정

- snapshot testing (HTML) — diff noise 주의

---

## 7. SEO 메타 테스트

### 확정

- 각 공개 페이지 타입별:
  - `<title>`, `meta name="description"`
  - `link rel="canonical"`
  - `meta property="og:*"`, twitter card
  - JSON-LD `application/ld+json` parse valid JSON
- robots meta `noindex` on admin/search (**향후** routes)

- [06-seo-strategy.md](06-seo-strategy.md) 체크리스트와 1:1 매핑 — **향후** `tests/test_seo_contract.py`

---

## 8. 크롤러 테스트

### 확정

- **fixture HTML/JSON** 파일 `tests/fixtures/crawl/`
- parser: title, url, published_at 추출
- upsert idempotency, UNIQUE conflict
- failure: timeout mock → run log failed, DB unchanged
- **no network** in CI (`pytest -m "not network"` **향후** marker)

### 향후 결정

- vcr.py cassettes (만료 주기 관리)

---

## 9. 관리자 테스트

### 확정

- unauthenticated `GET /admin/dashboard` → redirect login
- login success/failure, lockout after 5 fails
- POST without CSRF → 403
- POST logout with CSRF → session cleared
- role `viewer` cannot delete post
- audit log row created on coupon update (mock DB)

### 향후 결정

- full admin CRUD matrix parametrized

---

## 10. 보안 테스트

### 확정

- XSS: `q=<script>` in search → no unescaped script in body
- SQLi: `'; DROP--` in query → 200/empty, schema intact
- upload: evil binary → 400
- path traversal in static → 404

### 향후 결정

- OWASP ZAP baseline scan (staging)

---

## 11. 성능 테스트

### 확정

- **로컬 smoke:** home p95 < 500ms (cold DB, dev machine — 참고치만)
- N+1 query detection (**향후** sqlalchemy echo test)

### 향후 결정

- locust/k6 on staging
- Lighthouse CI (Core Web Vitals)

---

## 12. 정적 품질 (테스트 adjacent)

### 확정

- `ruff check`, `ruff format --check`
- `mypy app`
- `pre-commit run --all-files` (로컬 권장)
- `./scripts/lint.sh` (**확정**)

---

## 13. pytest 설정

### 확정 (`pyproject.toml`)

- `testpaths = ["tests"]`
- asyncio mode (**pytest-asyncio** when async routes grow)
- markers (향후): `slow`, `network`

### 향후 결정

- parallel `pytest-xdist`

---

## 14. CI (향후)

### 향후 결정

- GitHub Actions: lint + pytest on push/PR
- cache `.venv`, pip

### 확정 (로컬 게이트)

- PR 전 `./scripts/lint.sh && ./scripts/test.sh` 수동 실행

---

## 15. 배포 전 체크리스트

### 확정

- [ ] `pytest` green
- [ ] `ruff` + `mypy` green
- [ ] `APP_ENV=production` dry run settings validation
- [ ] `alembic upgrade head` on staging DB
- [ ] smoke: `/`, `/health`, `/robots.txt`, `/sitemap.xml`
- [ ] admin login + logout + CSRF
- [ ] `SECRET_KEY` not default on prod
- [ ] Nginx config `nginx -t`
- [ ] backup taken within 24h
- [ ] rollback tag/commit documented

### 향후 결정

- automated deploy hook runs checklist
- pip-audit clean

---

## 16. 테스트 데이터

### 확정

- factory functions in `tests/factories.py` (**향후** file)
- no production DB dump in repo
- seed minimal admin user in test fixture only

---

## 17. 관련 문서

- [09-security-strategy.md](09-security-strategy.md)
- [07-crawling-strategy.md](07-crawling-strategy.md)
- [11-deployment-strategy.md](11-deployment-strategy.md)
- [12-development-roadmap.md](12-development-roadmap.md) — 9단계 완료 조건

---

## 변경 이력

| 날짜 | 요약 |
|------|------|
| 2026-07-27 | 초안 작성 |
