# CLIPS 아키텍처

## 개요

CLIPS는 **단일 Python 애플리케이션**으로 공개 웹(SSR), SEO 엔드포인트, 헬스체크를 제공합니다. 프론트엔드 SPA를 기본으로 두지 않고 **서버에서 HTML을 완성**해 응답하는 **SEO-first SSR** 아키텍처를 채택합니다.

---

## 확정

### 아키텍처 스타일

- **모놀리식 FastAPI 앱** (`app/main.py` → `create_app()`)
- **레이어드 구조**: Router → Service → Repository → Model (ORM)
- **템플릿 렌더링**: Jinja2 (`app/templates/`, `get_templates()`)
- **설정**: Pydantic Settings (`app/config.py`, `.env`)
- **DB**: SQLAlchemy 2.x + Alembic 마이그레이션

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Client    │────▶│   FastAPI    │────▶│  Services   │────▶│   Repos  │
│ (Browser/   │     │  Routers +   │     │  (domain    │     │  (SQLA   │
│  Crawler)   │◀────│  Middleware  │◀────│   logic)    │◀────│  queries)│
└─────────────┘     └──────┬───────┘     └─────────────┘     └────┬─────┘
                           │                                        │
                           ▼                                        ▼
                    ┌──────────────┐                        ┌─────────────┐
                    │ Jinja2 HTML  │                        │ SQLite /    │
                    │ + /static    │                        │ PostgreSQL  │
                    └──────────────┘                        └─────────────┘
```

### SSR을 선택한 이유

| 관점 | SSR (확정) | CSR/SPA만 사용 시 단점 |
|------|------------|-------------------------|
| 크롤러 | HTML에 본문·메타 즉시 포함 | JS 실행·색인 지연, 메타 누락 위험 |
| Naver | 네이버 검색·웹마스터 도구가 HTML 메타에 의존 | 동적 메타 주입 불안정 |
| 성능 | 초기 페인트에 필요한 HTML만 전송 | JS 번들·hydration 비용 |
| 운영 | Python 한 스택으로 API·페이지 통합 | BFF·별도 Node 필요 |

**확정**: 공개 정보 페이지는 **항상 SSR**. 향후 관리자 UI만 부분적으로 HTMX 또는 경량 JS로 상호작용을 보강할 수 있음(본문 색인은 SSR 유지).

### 레이어 책임

| 레이어 | 경로(예) | 책임 |
|--------|----------|------|
| **Router** | `app/routers/web.py`, `seo.py`, `health.py` | HTTP 입출력, 상태 코드, `TemplateResponse`, 의존성 주입 |
| **Service** | `app/services/` | 도메인 규칙, SEO XML/JSON-LD 조립, 트랜잭션 경계 조율 |
| **Repository** | `app/repositories/` | 쿼리 캡슐화, N+1 방지, 페이지네이션 |
| **Model** | `app/models/` | SQLAlchemy 테이블·관계 |
| **Schema** | `app/schemas/` | Pydantic DTO (API·폼 검증) |
| **Core** | `app/core/` | 미들웨어, 로깅, 예외, 상수, 보안 검사 |
| **Templates** | `app/templates/` | HTML, `seo_meta.html` 등 |
| **Static** | `app/static/` | CSS 토큰, JS, 이미지, favicon |

**의존 방향(확정)**: Router → Service → Repository → Model. Template은 Router/Service가 context만 전달. Core는 하위 레이어를 import하지 않음.

### 요청 처리 흐름(공개 HTML)

1. **Ingress**: Uvicorn → FastAPI
2. **Middleware**: `SecurityHeadersMiddleware` → `RequestLoggingMiddleware`
3. **Routing**: `web.router` 등 매칭
4. **Handler**: Settings·상수 로드 → Service(필요 시) → `seo_context()` 병합
5. **Render**: `Jinja2Templates.TemplateResponse`
6. **Response**: `text/html` + 보안 헤더

**예외(확정)**:

- `404` + HTML Accept → `errors/404.html`, `robots: noindex, nofollow`
- 미처리 예외 → `errors/500.html`, `noindex`

### 데이터 흐름

**읽기(목표 패턴)**:

```
HTTP GET → Router → Service.get_*() → Repository → DB
                → seo_context + domain DTO → Template
```

**쓰기(관리자·크롤러, 향후 구현)**:

```
POST/PATCH → Router (auth) → Schema validate → Service
          → Repository → commit → redirect or JSON
```

**크롤 파이프(설계)**:

```
Scheduler/Worker → Crawler API → fetch official → parse
                → upsert notice/event/update → crawl_log
                → (optional) invalidate sitemap cache
```

### SEO·정적 자산

- `/robots.txt`, `/sitemap.xml`: `app/routers/seo.py` → `app/services/seo.py`
- JSON-LD: Service에서 dict 생성 → 템플릿 `application/ld+json`
- Static: `/static` 마운트 (`StaticFiles`)

### 캐시 포인트(설계)

| 위치 | 대상 | 정책 |
|------|------|------|
| `get_settings()` | Settings | 프로세스 LRU 캐시 |
| `get_templates()` | Jinja env | 프로세스 LRU 캐시 |
| HTTP CDN | `/static/*` | 장기 cache-control (향후) |
| 애플리케이션 | sitemap XML, 인기 목록 | TTL 5~60분 (향후 Redis) |
| DB | read-heavy slug 페이지 | optional materialized view (향후) |

**확정**: 현재는 **애플리케이션 레벨 캐시 없음**(sitemap은 요청 시 생성). 트래픽 증가 시 sitemap·목록 API부터 캐시 도입.

### 스케일링·배포(초안)

| 구성요소 | 로컬 | 스테이징/운영(권장) |
|----------|------|---------------------|
| App | `uvicorn app.main:app` | N replicas behind reverse proxy |
| DB | SQLite 파일 | **PostgreSQL** managed |
| Static | 앱과 동일 origin | CDN origin = app 또는 object storage |
| Secrets | `.env` | Secret manager / env inject |
| Migrations | `alembic upgrade head` | CI/CD deploy hook |

**확정**: 앱 인스턴스는 **stateless**(세션은 DB 또는 signed cookie). SQLite는 **로컬·테스트 전용**.

### 관측성(Observability)

- **로깅**: `RequestLoggingMiddleware` — method, path, status, duration_ms
- **헬스**: `/health` (라우터 `health.py`)
- **향후**: 구조화 JSON 로그, OpenTelemetry, Sentry

### 보안 기본선

- 운영 startup: `apply_startup_security_checks` — weak `SECRET_KEY`, debug 금지
- 응답 헤더: nosniff, `X-Frame-Options: DENY`, Referrer-Policy, Permissions-Policy, CSP Report-Only

---

## 향후 결정

- **Reverse proxy** (nginx, Caddy, Cloudflare) TLS 종료 및 HTTP/2/3
- **Worker 분리**: 크롤·이메일·통계 배치를 Celery/RQ vs cron container
- **Read replica** 및 connection pool sizing
- **Edge caching** HTML 여부 (개인화·noindex 페이지 제외 정책)
- **Admin** 별도 서브도메인 vs `/admin` path + IP allowlist

---

## 관련 문서

- [02-directory-structure.md](./02-directory-structure.md)
- [04-api-design.md](./04-api-design.md)
- [06-seo-strategy.md](./06-seo-strategy.md)
