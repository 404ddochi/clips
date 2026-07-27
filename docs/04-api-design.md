# CLIPS API·라우트 설계

## 개요

CLIPS는 **공개 SSR 라우트**를 중심으로 하고, JSON API는 관리·크롤·점진적 향상(HTMX)용으로 확장합니다. 현재 구현된 라우트와 **설계상 API**를 구분해 기술합니다.

---

## 확정

### URL 네이밍

- 공개 페이지: **kebab-case 경로**, 소문자 (`/guides`, `/coupons`)
- 상세(향후): `/{section}/{slug}` — slug는 `[a-z0-9-]` (한글 slug는 **향후 결정**)
- API: `/api/v1/...`, 크롤러: `/api/crawler/v1/...`
- Trailing slash: **없음** (`APP_BASE_URL`도 trailing strip)

### Web Routes (SSR, HTML)

| Method | Path | name | 상태 | robots(기본) |
|--------|------|------|------|----------------|
| GET | `/` | home | **구현** | index, follow |
| GET | `/news` | news | preparing | noindex, follow |
| GET | `/classes` | classes | preparing | noindex, follow |
| GET | `/contents` | contents | preparing | noindex, follow |
| GET | `/items` | items | preparing | noindex, follow |
| GET | `/bosses` | bosses | preparing | noindex, follow |
| GET | `/maps` | maps | preparing | noindex, follow |
| GET | `/guides` | guides | preparing | noindex, follow |
| GET | `/coupons` | coupons | preparing | noindex, follow |

**공통 응답**: `text/html; charset=utf-8`, `TemplateResponse`, context에 `nav_items`, `active_nav`, `seo_*`.

**향후 Web Routes (설계)**:

| Path | 설명 |
|------|------|
| `/news/{slug}` | 공지·이벤트·업데이트 통합 또는 분리 |
| `/classes/{slug}` | 클래스 상세 + 스킬 목록 |
| `/items/{slug}` | 아이템 상세 |
| `/bosses/{slug}` | 보스 상세 |
| `/guides/{slug}` | 공략 |
| `/search` | SSR 검색 결과 (`q` query) |
| `/faq` | FAQPage |

### SEO Routes

| Method | Path | Content-Type | 상태 |
|--------|------|--------------|------|
| GET | `/robots.txt` | text/plain | **구현** |
| GET | `/sitemap.xml` | application/xml | **구현** (현재 `/` only) |

### Health

| Method | Path | 응답 | 상태 |
|--------|------|------|------|
| GET | `/health` | JSON `{"status":"ok"}` | **구현** |

### Internal API (JSON, 향후)

**목적**: 같은 origin HTMX/fetch, 모바일 앱 **미우선**.

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/search` | `q`, `type`, pagination |
| GET | `/api/v1/notices` | 목록 JSON (캐시 friendly) |
| GET | `/api/v1/classes/{slug}` | 상세 |

**인증**: 공개 read는 무인증. rate limit by IP — **향후 결정**.

### Admin API (향후)

**Prefix**: `/api/admin/v1` 또는 `/admin/api/v1`

| Method | Path | 설명 |
|--------|------|------|
| POST | `/auth/login` | session cookie or JWT |
| CRUD | `/notices`, `/guides`, ... | Schema validated body |
| POST | `/publish/{entity}/{id}` | status → published, sitemap bump |

**인증(확정 방향)**:

- Session cookie (HttpOnly, Secure, SameSite=Lax) + CSRF on mutating forms
- Role: `admin`, `moderator`

### Crawler API (향후)

**Prefix**: `/api/crawler/v1`

| Method | Path | 설명 |
|--------|------|------|
| POST | `/jobs/run` | source_id trigger |
| GET | `/jobs/{id}` | status |
| POST | `/webhook/official` | push notification if ever available |

**인증(확정 방향)**: Bearer token or HMAC signature header; **공개 노출 금지**.

---

## 응답 규칙

### HTML

- Status: RESTful (404, 500 handlers with branded pages for HTML Accept)
- `Accept`: `text/html` 포함 시 에러도 HTML (`main.py` `_wants_html`)

### JSON (향후 표준 envelope)

```json
{
  "data": {},
  "meta": { "page": 1, "page_size": 20, "total": 100 },
  "errors": null
}
```

**확정**: list endpoint는 **`meta` pagination** 필수.

### Error JSON

| HTTP | code | meaning |
|------|------|---------|
| 400 | `validation_error` | Pydantic detail |
| 401 | `unauthorized` | |
| 403 | `forbidden` | |
| 404 | `not_found` | |
| 429 | `rate_limited` | |
| 500 | `internal_error` | message generic in prod |

**확정**: production 500 body에 stack trace **금지**.

---

## 페이지네이션 (확정)

- Query: `page` (1-based), `page_size` (default 20, max 100)
- SSR 목록: 동일 query string + `<link rel="prev/next">` **향후**
- Response header: `X-Total-Count` optional for API

---

## 버전 관리

| 영역 | 정책 |
|------|------|
| Public HTML | **버전 없음** — URL 영구성 |
| JSON API | `/api/v1` prefix; breaking change 시 v2 병행 6개월 |
| Crawler API | 독립 version |

---

## CORS·캐시

- **확정**: SSR same-origin; CORS default deny.
- API public read: `Cache-Control: public, max-age=60` (향후 CDN).
- Admin: `no-store`.

---

## OpenAPI

- FastAPI auto `/docs` — **production에서는 비활성화**(향후 middleware gate).

---

## 향후 결정

- GraphQL 도입 여부 (**기본 거부**)
- Webhook outbound (Discord 공지 알림)
- API key for third-party partners
- idempotency-key on POST (coupon sync)

---

## 관련 문서

- [01-architecture.md](./01-architecture.md)
- [03-database-design.md](./03-database-design.md)
- [06-seo-strategy.md](./06-seo-strategy.md)
