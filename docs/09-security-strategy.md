# 09. 보안 전략

CLIPS는 공개 SSR 사이트와 **관리자 영역**을 동시에 운영한다. 본 문서는 위협 모델, 통제, 운영 습관을 정의한다. 내용은 **유사 규모 게임 정보 사이트 운영 경험**(세션·CSRF·업로드·엣지 rate limit·감사 로그 등)을 **일반화**해 반영하며, **타 프로젝트 코드·설정을 복사하지 않는다.**

**범례:** **확정** / **향후 결정**

---

## 1. 위협 모델 (요약)

| 위협 | 노출면 | 우선순위 |
|------|--------|----------|
| 관리자 계정 탈취 | `/admin/*` | 높음 |
| XSS (저장/반사) | Jinja 출력, 검색 하이라이트 | 높음 |
| CSRF | 관리자 POST, 상태 변경 | 높음 |
| SQL Injection | SQLAlchemy 쿼리 | 중 (ORM 사용 시 낮음, raw SQL 주의) |
| 악성 파일 업로드 | 배너·이미지 | 중 |
| SSRF | 크롤러 fetch URL | 중 (5단계) |
| 정보 유출 | 에러 페이지, 로그, `.env` | 중 |
| DoS / brute force | login, search, crawl | 중 |

---

## 2. CSRF

### 확정

- **모든 관리자 상태 변경 POST/PUT/PATCH/DELETE**에 CSRF 토큰 검증
- 토큰: 세션 바인딩, per-form 또는 per-session rotation — **구현 시 하나로 통일**
- 로그아웃은 **POST only** + CSRF
- 공개 읽기 전용 GET은 CSRF 대상 아님

### 향후 결정

- Double Submit Cookie vs synchronizer token
- SameSite=Strict for admin only

---

## 3. XSS (Cross-Site Scripting)

### 확정

- Jinja2 **autoescape 기본 ON** — `| safe` 사용 최소화, 사용 시 코드 리뷰 필수
- 사용자·관리자 입력 HTML **저장 금지**(plain text); 필요 시 서버 측 sanitizer **향후** 도입
- 검색 하이라이트: **escape 후** `<mark>` 삽입 (순서 고정)
- `Content-Security-Policy` — **향후 결정** nonce/hash; 초기에는 report-only 검토
- JSON-LD는 **구조화 데이터 빌더**로 생성, raw HTML 삽입 금지

---

## 4. SQL Injection

### 확정

- **SQLAlchemy 2.x ORM / Core bound parameters**만 사용
- f-string SQL **금지**; raw text는 `text()` + named params
- 정렬·컬럼명 화이트리스트 (admin 목록 sort key)
- SQLite → PostgreSQL 이전 시에도 동일 규칙

### 향후 결정

- sqlfluff / 정적 분석 hook

---

## 5. 파일 업로드 검증

### 확정

- 허용 확장자: **jpg, jpeg, png, webp, gif** (SVG **금지** — embedded script)
- 검증 단계: 확장자, `Content-Type`, **최대 5MB**, **Pillow verify** (실제 디코딩)
- 저장 경로: `uploads/` — `.gitignore`, 웹 root **직접 실행 불가** (Nginx `alias` + `location` 제한)
- 파일명: UUID + 확장자 (원본명 저장 금지)

### 향후 결정

- AV 스캔 (ClamAV)
- WebP re-encode로 EXIF strip

---

## 6. 인증 및 세션

### 확정

- 관리자: **서버 세션** + HttpOnly 쿠키
- 운영: `APP_ENV=production` 시 `validate_settings` — **SECRET_KEY 기본값·APP_DEBUG=true 시작 차단** (현재 `app/config.py` **확정**)
- 세션 재생성: **로그인 성공 시** session ID rotate
- 공개 사용자 로그인(7단계): 동일 원칙, 별도 쿠키 이름

### 향후 결정

- `ADMIN_SESSION_MAX_AGE_SECONDS` (예: 28800)
- idle timeout
- Redis session store

---

## 7. 비밀번호 해시

### 확정

- **bcrypt** 또는 **argon2id** (Python `passlib` 또는 `argon2-cffi`) — 구현 3단계에서 **하나 선택**
- 평문·MD5·SHA1 저장 **금지**
- 로그인 실패 메시지: **“아이디 또는 비밀번호가 올바르지 않습니다”** (어느 쪽 틀렸는지 구분 안 함)

### 향후 결정

- 비밀번호 정책(길이, zxcvbn)
- 초기 admin bootstrap CLI

---

## 8. 관리자 접근 제한

### 확정

- **IP allowlist** — **향후 결정**(VPN 운영 시); 기본은 인증 + rate limit
- 로그인 실패: **5회 / 10분 / IP** 앱 레벨 차단
- Nginx: `/admin/login` **limit_req** (예: 5r/m, burst 5) — **운영 확정 권장**
- IP 식별: **`request.client.host`** — X-Forwarded-For **단독 신뢰 금지**; Nginx `real_ip` 설정 후 trusted proxy만

### 향후 결정

- geo block
- admin URL prefix secret path (security by obscurity 보조)

---

## 9. Rate Limit

### 확정

| 대상 | 정책 |
|------|------|
| `/admin/login` | 앱 5/10min + Nginx limit_req |
| 공개 검색 | **향후** 30/min/IP |
| `/health` | 무제한 (모니터링) |
| 크롤 수동 실행 | 관리자 1/min |

- 다중 worker 시 앱 메모리 limit **불완전** → **엣지(Nginx) + DB/Redis** 확장 검토 (**향후 결정**)

---

## 10. 보안 HTTP 헤더

### 확정 (Nginx 또는 middleware)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (또는 `SAMEORIGIN`)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` — camera/mic/geolocation deny
- HSTS: **HTTPS 적용 후** `max-age=31536000; includeSubDomains`

### 향후 결정

- CSP enforce
- COOP/COEP

---

## 11. 환경변수

### 확정

- `.env` **Git 제외**, `.env.example`만 커밋
- production secrets: **서버 파일** 또는 secret manager — repo에 없음
- 필수: `SECRET_KEY`, `DATABASE_URL`, `APP_BASE_URL`
- 앱 시작 시 production insecure default **fail-fast** (구현됨)

### 향후 결정

- `CRAWLER_*`, `ADMIN_*`, Sentry DSN 분리

---

## 12. 로그 민감정보 제거 (redaction)

### 확정

- 로그에 **비밀번호, 세션 ID, CSRF, Authorization, Cookie 전체** 출력 금지
- SQLAlchemy echo **production off**
- 크롤: **응답 body 전체** DEBUG 로그 금지
- structlog/filter: key 이름 `password`, `token`, `secret` 마스킹

### 향후 결정

- centralized log scrubber
- PII retention 정책 문서 ([PRIVACY] 향후)

---

## 13. 에러 메시지 노출 제한

### 확정

- 공개 500: **일반 메시지** + request id (선택); stack trace **미노출**
- `APP_DEBUG=true`는 **local/staging only**; production 시작 차단
- API JSON error: `{ "detail": "..." }` — 내부 예외 타입 숨김
- 404: 경로 존재 여부 힌트 최소화

---

## 14. 백업

### 확정

- PostgreSQL/SQLite: **일일 논리 백업** ( retention **14~30일** — **향후 결정**)
- 백업 파일 권한 `600`, off-site 복사
- **복구 리허설** 분기 1회 (체크리스트 [11-deployment-strategy.md](11-deployment-strategy.md))

### 향후 결정

- WAL 아카이브, point-in-time recovery

---

## 15. 의존성 점검

### 확정

- `pip-audit` 또는 `uv pip audit` — **릴리스 전·월 1회**
- Dependabot/Renovate — **향후 결정**
- pre-commit: Ruff, mypy (현재 **확정**)
- CVE 발견 시: **패치 → test → deploy**; 긴급 시 admin read-only 모드 검토

---

## 16. 크롤러·SSRF (5단계 연동)

### 확정

- fetch URL은 **화이트리스트 도메인**만
- private IP, metadata URL(169.254.x) **차단**
- redirect 최대 3회, scheme `http/https` only

### 향후 결정

- DNS rebinding 방어 (resolve 후 IP 검사)

---

## 17. HTTPS 및 네트워크

### 확정

- 운영: **TLS 종료 Nginx**, 앱은 localhost Uvicorn
- 방화벽: 80/443 only public; DB port **비공개**

---

## 18. 보안 테스트 (10-testing-strategy.md)

### 확정

- CSRF 없는 POST → 403
- login brute force → 429/차단
- XSS payload in search → escaped
- upload `.php` disguised → reject

---

## 19. 사고 대응 (간략)

### 확정

- SECRET_KEY 유출: **즉시 rotate**, 세션 전체 invalidate
- admin compromise: 비밀번호 reset, audit log 검토, backup 무결성 확인

### 향후 결정

- 공지 템플릿, 연락처

---

## 변경 이력

| 날짜 | 요약 |
|------|------|
| 2026-07-27 | 초안 작성 |
