# Release Readiness

점검 일자: 2026-07-29  
대상 commit: `d20c9d0` (작업 시점 `master`)  
실행 환경: Python 3.14.6 · FastAPI 0.140.1 · Uvicorn 0.51.0 · pytest / ruff / mypy

최종 판정: **READY WITH WARNINGS**

공개 SSR 허브·SEO·검색·보안 기본 통제는 배포 가능 상태다.  
다만 실데이터·관리자·인프라(Nginx/systemd)는 아직 미완이며, 운영에서는 빈 목록·준비 중 UI가 노출된다.

---

## 1. Blocker (즉시 수정 완료)

| 이슈 | 조치 |
|------|------|
| Mock 소식·패치·쿠폰이 운영에 노출 | `allows_demo_content()` — production에서 catalogue/상세/sitemap 비노출 |
| Mock UI 문구(CLIPS-DEMO 등) 운영 노출 | 쿠폰/소식 안내 문구를 demo 전용으로 분리 |
| production `SITE_URL` localhost/http 허용 | `validate_settings` — https + non-loopback fail-fast |
| OpenAPI(`/docs`) 운영 노출 | 생성 시 비활성 + request-time block middleware |

---

## 2. Warning (배포 가능, 빠른 개선 권고)

| 우선순위 | 항목 | 영향 | 권장 조치 |
|----------|------|------|-----------|
| P1 | TrustedHost / HSTS | Host spoofing·HTTPS 강제 | Nginx 또는 앱에 TrustedHost·HSTS |
| P1 | 실데이터 없음 | 소식/쿠폰 빈 목록 | CMS/DB 연동 후 seed |
| P1 | Alembic revisions 0건 | DB 스키마 미정 | 모델 확정 후 migration |
| P1 | 관리자 미구현 | 콘텐츠 운영 불가 | admin + CSRF (docs/08) |
| P2 | CSP 미설정 | XSS 방어 약화 | report-only → enforce |
| P2 | static cache bust | CSS/JS 캐시 잔존 | `?v=` 또는 filename hash |
| P2 | 비-404 HTTPException HTML이 `detail` 노출 | 내부 메시지 유출 가능 | 일반 문구로 교체 |
| P2 | CORS/세션 | 현재 SSR-only로 낮음 | API·admin 도입 시 재검토 |
| P3 | docs SEO 문서 drift | 문서·코드 불일치 | docs/06 갱신 |

---

## 3. Pass (확인됨)

- 공개 hub URL 200, 잘못된 경로 404 + noindex
- `/dev/design-system` production 404
- search `noindex, follow` · SearchAction `q={search_term_string}`
- robots Disallow `/admin` `/dev` `/api` · staging `Disallow: /`
- sitemap 절대 URL · search/admin/dev 제외 · draft guide 제외
- JSON-LD WebSite / Organization / SearchAction / Breadcrumb / Article 규칙
- Security headers: nosniff, SAMEORIGIN, Referrer-Policy, Permissions-Policy
- `.env` gitignore · SECRET_KEY/APP_DEBUG production fail-fast
- 클래스 공개명 외 아이템·보스·지도·공략 가짜 상세 없음
- skip link · `lang="ko"` · main landmark · theme toggle

---

## 4. 운영 환경변수

| 변수 | 필수 | 기본값 | 운영 권장 | 비밀 |
|------|------|--------|-----------|------|
| `APP_ENV` | 예 | `local` | `production` | 아니오 |
| `APP_DEBUG` | 예 | `false` | `false` | 아니오 |
| `SITE_URL` | 예 | `http://127.0.0.1:8001` | `https://실제도메인` | 아니오 |
| `APP_BASE_URL` | 선택(호환) | 동일 | SITE_URL과 동일 | 아니오 |
| `SECRET_KEY` | 예 | `change-me` | 강한 난수 | **예** |
| `DATABASE_URL` | 예 | sqlite 로컬 | PostgreSQL | **예** |
| `APP_NAME` | 선택 | CLIPS | CLIPS | 아니오 |
| `APP_HOST` / `APP_PORT` | 선택 | 127.0.0.1:8001 | 127.0.0.1:8000 (프록시 뒤) | 아니오 |
| `DEFAULT_LOCALE` | 선택 | ko | ko | 아니오 |
| `TIMEZONE` | 선택 | Asia/Seoul | Asia/Seoul | 아니오 |

누락/오설정 시:

- production + `SECRET_KEY=change-me` → **startup fail**
- production + `APP_DEBUG=true` → **startup fail**
- production + http/localhost `SITE_URL` → **startup fail**

코드에 없는 값(추측 금지): `TRUSTED_HOSTS`, `ALLOWED_ORIGINS`, 관리자 계정 env, 외부 API key.

---

## 5. 배포 순서 (문서상 권장 — 인프라 파일은 저장소에 없음)

확인됨: `docs/11-deployment-strategy.md` (Ubuntu + Nginx + systemd + uvicorn).  
저장소에 Dockerfile / nginx conf / systemd unit / `scripts/deploy.sh` **없음** → 인프라 검증은 서버 측 확인 필요.

배포 전:

1. git clean · target tag/commit
2. `APP_ENV=production` · `APP_DEBUG=false` · `SITE_URL=https://…` · 강한 `SECRET_KEY`
3. `ruff` / `mypy app` / `pytest`
4. DB backup (PostgreSQL 사용 시)

배포:

1. `git fetch && git checkout <tag>`
2. `pip install -e .` (production deps)
3. `alembic upgrade head` (revision 생기면)
4. `systemctl restart clips`
5. `curl -sf http://127.0.0.1:8000/health`

배포 후 확인 URL:

- `/` `/search` `/news` `/coupons` `/robots.txt` `/sitemap.xml`
- 존재하지 않는 경로 404
- `/dev/design-system` 404
- `/docs` 404
- canonical·sitemap에 localhost 없음
- 홈 JSON-LD SearchAction

Rollback:

1. 이전 tag checkout
2. migrate downgrade 가능 여부 확인 (현재 revision 0 → N/A)
3. restart · `/health`

---

## 6. 미확인 인프라 항목

- Nginx TLS / HSTS / static cache
- systemd unit · workers · restart policy
- PostgreSQL backup · log rotation
- deploy user · filesystem permission
- health check 모니터링

---

## 7. 실데이터 공개 후 할 일

1. Mock catalogue를 DB/CMS로 교체 (또는 seed를 실데이터로)
2. `allows_demo_content` 경로에 실데이터 소스 연결
3. 아이템·보스·지도·공략 공개 시 sitemap detail 자동 포함 확인
4. 관리자·CSRF·세션 쿠키(Secure/HttpOnly/SameSite)
5. TrustedHost + CSP
6. Alembic migration · rollback 런북

---

## 8. 자동 점검

- `tests/test_release_readiness.py`
  - 공개 hub 200
  - sitemap URL 200 · search/admin/dev 제외
  - production demo 비노출
  - SITE_URL fail-fast
  - staging robots
  - 내부 nav 링크
  - static / security headers
